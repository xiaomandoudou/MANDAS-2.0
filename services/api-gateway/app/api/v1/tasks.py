from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Set
import uuid
from datetime import datetime

from app.core.database import get_db, Task
from app.core.redis_client import publish_task_to_queue
from app.core.auth import get_current_user
from loguru import logger

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
    
    async def broadcast_to_task(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.active_connections[task_id].discard(conn)

manager = ConnectionManager()


class TaskCreate(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = {}


class TaskResponse(BaseModel):
    id: str
    user_id: str
    status: str
    prompt: str
    plan: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[TaskResponse]


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task_id = uuid.uuid4()
    priority = task_data.config.get("priority", 5)
    
    new_task = Task(
        id=task_id,
        user_id=uuid.UUID(current_user["sub"]),
        prompt=task_data.prompt,
        config=task_data.config,
        priority=priority
    )
    
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    success = await publish_task_to_queue(str(task_id), priority)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue task"
        )
    
    logger.info(f"Task {task_id} created and queued for user {current_user['username']}")
    
    return {
        "task_id": str(task_id),
        "status": "QUEUED",
        "message": "任务已成功提交，正在排队等待处理。",
        "created_at": new_task.created_at.isoformat()
    }


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    
    result = await db.execute(
        select(Task).where(
            Task.id == task_uuid,
            Task.user_id == uuid.UUID(current_user["sub"])
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    plan_steps = []
    if task.plan:
        plan_steps = task.plan.get("steps", [])
    
    return {
        "id": str(task.id),
        "user_id": str(task.user_id),
        "status": task.status,
        "prompt": task.prompt,
        "plan": plan_steps,
        "result": task.result,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat()
    }


@router.get("/")
async def list_tasks(
    page: int = 1,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit
    
    query = select(Task).where(Task.user_id == uuid.UUID(current_user["sub"]))
    
    if status_filter:
        query = query.where(Task.status == status_filter)
    
    query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    count_query = select(Task).where(Task.user_id == uuid.UUID(current_user["sub"]))
    if status_filter:
        count_query = count_query.where(Task.status == status_filter)
    
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    task_items = []
    for task in tasks:
        task_items.append({
            "id": str(task.id),
            "user_id": str(task.user_id),
            "status": task.status,
            "prompt": task.prompt[:100] + "..." if len(task.prompt) > 100 else task.prompt,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": task_items
    }


@router.websocket("/{task_id}/stream")
async def websocket_task_stream(websocket: WebSocket, task_id: str):
    try:
        task_uuid = uuid.UUID(task_id)
        await manager.connect(websocket, task_id)
        
        async for db in get_db():
            result = await db.execute(select(Task).where(Task.id == task_uuid))
            task = result.scalar_one_or_none()
            if task:
                await websocket.send_json({
                    "type": "task_state",
                    "payload": {
                        "task_id": task_id,
                        "status": task.status,
                        "plan": task.plan
                    }
                })
                
                if task.plan:
                    await websocket.send_json({
                        "type": "plan_generated",
                        "payload": {
                            "plan_id": task.plan.get("plan_id"),
                            "task_id": task_id,
                            "summary": task.plan.get("summary", "执行计划已生成"),
                            "version": task.plan.get("version", "v1"),
                            "steps": task.plan.get("steps", [])
                        }
                    })
            break
        
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
                
    except ValueError:
        await websocket.send_json({"error": "Invalid task ID format"})
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket, task_id)

@router.get("/{task_id}/plan")
async def get_task_plan(
    task_id: str,
    include_result: bool = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task execution plan with optional result previews"""
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    
    result = await db.execute(
        select(Task).where(
            Task.id == task_uuid,
            Task.user_id == uuid.UUID(current_user["sub"])
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if not task.plan:
        return {
            "plan_id": None,
            "task_id": task_id,
            "summary": "任务无需规划，直接进入执行阶段。",
            "version": "v1",
            "steps": []
        }
    
    plan_data = task.plan
    if include_result:
        for step in plan_data.get("steps", []):
            if "result_preview" not in step:
                step["result_preview"] = None
    else:
        for step in plan_data.get("steps", []):
            step.pop("result_preview", None)
    
    return plan_data


@router.post("/{task_id}/plan/regenerate")
async def regenerate_task_plan(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate task plan with new version"""
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    
    result = await db.execute(
        select(Task).where(
            Task.id == task_uuid,
            Task.user_id == uuid.UUID(current_user["sub"])
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    current_version = task.plan.get("version", "v1") if task.plan else "v1"
    version_num = int(current_version.replace("v", "")) + 1
    new_version = f"v{version_num}"
    
    await publish_task_to_queue(f"regenerate_plan:{task_id}", 1)
    
    await manager.broadcast_to_task(task_id, {
        "type": "plan_regeneration_started",
        "payload": {
            "task_id": task_id,
            "new_version": new_version
        }
    })
    
    return {
        "task_id": task_id,
        "message": "Regeneration started.",
        "plan_version": new_version
    }


@router.put("/tasks/{task_id}/plan/steps/{step_id}")
async def update_plan_step(
    task_id: str,
    step_id: int,
    step_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Internal endpoint for updating plan step status"""
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    
    result = await db.execute(select(Task).where(Task.id == task_uuid))
    task = result.scalar_one_or_none()
    
    if not task or not task.plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task or plan not found"
        )
    
    plan = task.plan
    steps = plan.get("steps", [])
    
    for step in steps:
        if step.get("step_id") == step_id:
            step.update({
                "status": step_data.get("status", step.get("status")),
                "result_preview": step_data.get("result_preview"),
                "started_at": step_data.get("started_at"),
                "completed_at": step_data.get("completed_at"),
                "retry_count": step_data.get("retry_count", step.get("retry_count", 0))
            })
            break
    
    await db.execute(
        update(Task)
        .where(Task.id == task_uuid)
        .values(plan=plan)
    )
    await db.commit()
    
    await manager.broadcast_to_task(task_id, {
        "type": "step_status_update",
        "payload": {
            "step_id": step_id,
            "status": step_data.get("status"),
            "result_preview": step_data.get("result_preview"),
            "started_at": step_data.get("started_at"),
            "completed_at": step_data.get("completed_at"),
            "retry_count": step_data.get("retry_count", 0)
        }
    })
    
    return {"status": "updated"}


@router.post("/{task_id}/broadcast")
async def broadcast_websocket_event(
    task_id: str,
    event: dict,
    current_user: dict = Depends(get_current_user)
):
    try:
        await manager.broadcast_to_task(task_id, event)
        return {"status": "broadcasted"}
    except Exception as e:
        logger.error(f"Failed to broadcast event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast event"
        )
