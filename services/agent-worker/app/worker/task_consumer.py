import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from app.core.config import settings
from app.core.database import get_db, Task
from app.core.redis_client import get_redis
from app.agents.agent_manager import AgentManager
from app.tools.tool_executor import ToolExecutor


class TaskConsumer:
    def __init__(self):
        self.redis_client = None
        self.agent_manager = None
        self.tool_executor = None
        self.running = False
        self.websocket_url = f"http://api-gateway:8080/mandas/v1/tasks"
    
    async def broadcast_step_update(self, task_id: str, step_update: Dict[str, Any]):
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.websocket_url}/{task_id}/broadcast",
                    json={
                        "type": "step_status_update",
                        "payload": step_update
                    }
                )
        except Exception as e:
            logger.error(f"Failed to broadcast step update: {e}")
    
    async def broadcast_log(self, task_id: str, log_entry: Dict[str, Any]):
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.websocket_url}/{task_id}/broadcast",
                    json={
                        "type": "log",
                        "payload": log_entry
                    }
                )
        except Exception as e:
            logger.error(f"Failed to broadcast log: {e}")

    async def initialize(self):
        self.redis_client = await get_redis()
        
        from app.core.tools.tool_registry import ToolRegistry
        from app.core.security.execution_guard import ExecutionGuard
        from app.agents.router.llm_router_agent import LLMRouterAgent
        from app.agents.manager.group_chat_manager import MandasGroupChatManager
        from app.memory.memory_manager import MemoryManager
        from app.llm.llm_router import LLMRouter
        
        self.memory_manager = MemoryManager()
        self.tool_registry = ToolRegistry(getattr(settings, 'tools_directory', '/app/tools.d'))
        self.execution_guard = ExecutionGuard(self.tool_registry)
        self.llm_router = LLMRouter()
        self.llm_router_agent = LLMRouterAgent(self.llm_router)
        self.group_chat_manager = MandasGroupChatManager(
            self.tool_registry, self.execution_guard, self.memory_manager
        )
        
        await self.memory_manager.initialize()
        await self.execution_guard.initialize()
        await self.tool_registry.initialize()
        await self.llm_router.initialize()
        await self.llm_router_agent.initialize()
        
        self.agent_manager = AgentManager()
        self.tool_executor = ToolExecutor()
        await self.agent_manager.initialize()
        await self.tool_executor.initialize()
        
        logger.info("Task Consumer with V0.6 modules initialized successfully")

    async def start_consuming(self):
        self.running = True
        logger.info("Starting task consumption from Redis Stream")
        
        while self.running:
            try:
                messages = await self.redis_client.xreadgroup(
                    settings.redis_consumer_group,
                    settings.redis_consumer_name,
                    {settings.redis_task_stream: ">"},
                    count=1,
                    block=1000
                )
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        await self.process_message(msg_id, fields)
                        
            except Exception as e:
                logger.error(f"Error in task consumption loop: {e}")
                await asyncio.sleep(5)

    async def process_message(self, msg_id: str, fields: Dict[str, str]):
        task_id = fields.get("task_id")
        if not task_id:
            logger.error(f"No task_id in message {msg_id}")
            return

        logger.info(f"Processing task {task_id} from message {msg_id}")
        
        try:
            async for db in get_db():
                result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
                task = result.scalar_one_or_none()
                
                if not task:
                    logger.error(f"Task {task_id} not found in database")
                    await self.ack_message(msg_id)
                    return
                
                if task.status != "QUEUED":
                    logger.warning(f"Task {task_id} is not in QUEUED status: {task.status}")
                    await self.ack_message(msg_id)
                    return
                
                await self.execute_task(db, task)
                await self.ack_message(msg_id)
                
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            await self.handle_task_error(task_id, str(e))

    async def execute_task(self, db: AsyncSession, task: Task):
        task_id = str(task.id)
        logger.info(f"Executing task {task_id}: {task.prompt[:100]}...")
        
        try:
            await db.execute(
                update(Task)
                .where(Task.id == task.id)
                .values(status="RUNNING", updated_at=func.now())
            )
            await db.commit()
            
            await self._pre_process_task(task_id, task.prompt, task.config or {})
            
            available_tools = [tool.name for tool in self.tool_registry.list_tools()]
            routing_decision = await self.llm_router_agent.decide(
                task.prompt, available_tools, {"task_id": task_id}
            )
            
            logger.info(f"Routing decision for task {task_id}: {routing_decision}")
            
            if routing_decision.get("complexity") == "high" or len(available_tools) > 0:
                result = await self.group_chat_manager.process_task(task_id, task.prompt, task.config or {})
            else:
                # 降级到原有AgentManager
                result = await self.agent_manager.process_task(
                    task_id=task_id,
                    prompt=task.prompt,
                    config=task.config or {}
                )
            
            await self._post_execute(task_id, result)
            
            await db.execute(
                update(Task)
                .where(Task.id == task.id)
                .values(
                    status="COMPLETED",
                    result=result,
                    updated_at=func.now()
                )
            )
            await db.commit()
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}")
            
            await self._on_failure(task_id, str(e))
            
            retry_count = task.retry_count + 1
            if retry_count < settings.max_retry_count:
                await db.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(
                        status="QUEUED",
                        retry_count=retry_count,
                        updated_at=func.now()
                    )
                )
                logger.info(f"Task {task_id} queued for retry ({retry_count}/{settings.max_retry_count})")
            else:
                await db.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(
                        status="FAILED",
                        result={"error": str(e)},
                        updated_at=func.now()
                    )
                )
                logger.error(f"Task {task_id} failed after {settings.max_retry_count} retries")
            
            await db.commit()

    async def handle_task_error(self, task_id: str, error: str):
        try:
            async for db in get_db():
                await db.execute(
                    update(Task)
                    .where(Task.id == uuid.UUID(task_id))
                    .values(
                        status="FAILED",
                        result={"error": error},
                        updated_at=func.now()
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update task {task_id} error status: {e}")

    async def ack_message(self, msg_id: str):
        try:
            await self.redis_client.xack(
                settings.redis_task_stream,
                settings.redis_consumer_group,
                msg_id
            )
        except Exception as e:
            logger.error(f"Failed to acknowledge message {msg_id}: {e}")

    async def stop(self):
        self.running = False
        logger.info("Task Consumer stopped")

    async def _pre_process_task(self, task_id: str, prompt: str, config: Dict[str, Any]):
        """V0.6: Pre-process hook for task initialization"""
        try:
            await self.memory_manager.remember(
                task_id, 
                {
                    "role": "system",
                    "content": f"Task {task_id} started: {prompt[:100]}...",
                    "name": "TaskConsumer"
                },
                short_term=True
            )
            
            logger.info(f"Pre-processed task {task_id}")
            
        except Exception as e:
            logger.error(f"Error in pre-process for task {task_id}: {e}")
    
    async def _post_execute(self, task_id: str, result: Dict[str, Any]):
        """V0.6: Post-execute hook for result processing"""
        try:
            await self.memory_manager.remember(
                task_id,
                {
                    "role": "system", 
                    "content": f"Task {task_id} completed with status: {result.get('status')}",
                    "name": "TaskConsumer"
                },
                short_term=True,
                long_term=True
            )
            
            logger.info(f"Post-processed task {task_id}")
            
        except Exception as e:
            logger.error(f"Error in post-execute for task {task_id}: {e}")
    
    async def _on_failure(self, task_id: str, error: str):
        """V0.6: On-failure hook for error handling"""
        try:
            await self.memory_manager.remember(
                task_id,
                {
                    "role": "system",
                    "content": f"Task {task_id} failed: {error}",
                    "name": "TaskConsumer"
                },
                short_term=True,
                long_term=True
            )
            
            logger.error(f"Task {task_id} failure recorded")
            
        except Exception as e:
            logger.error(f"Error in failure handler for task {task_id}: {e}")


from sqlalchemy.sql import func
