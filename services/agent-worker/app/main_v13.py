import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger

from app.core.smart_llm_client import SmartLLMClient
from app.core.planning.planner import TaskPlanner
from app.llm.llm_router import LLMRouter


app = FastAPI(title="MANDAS Agent Worker V1.3", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

smart_client = None
task_planner = None


class PlanRequest(BaseModel):
    task_id: str
    prompt: str
    config: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, str]


@app.on_event("startup")
async def startup_event():
    global smart_client, task_planner
    
    logger.info("Starting MANDAS Agent Worker V1.3...")
    
    try:
        smart_client = SmartLLMClient()
        await smart_client.initialize()
        
        llm_router = LLMRouter()
        await llm_router.initialize()
        task_planner = TaskPlanner(llm_router)
        
        logger.info("V1.3 Agent Worker initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize V1.3 components: {e}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.3.0",
        components={
            "smart_client": "available" if smart_client else "unavailable",
            "task_planner": "available" if task_planner else "unavailable"
        }
    )


@app.get("/test")
async def test_endpoint():
    """Test endpoint for V1.3 functionality"""
    
    if not smart_client:
        raise HTTPException(status_code=503, detail="SmartLLMClient not available")
    
    test_prompt = "请帮我分析一个Python项目的代码结构，生成文档，并创建测试用例"
    test_config = {"task_id": "test-task", "priority": 5}
    
    try:
        plan = await smart_client.generate_plan(test_prompt, test_config)
        
        return {
            "status": "success",
            "message": "V1.3 TaskPlanner功能测试成功",
            "test_plan": plan,
            "components": {
                "smart_client": "working",
                "plan_generation": "working",
                "steps_count": len(plan.get("steps", []))
            }
        }
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@app.post("/plan")
async def generate_plan(request: PlanRequest):
    """Generate task plan using V1.3 TaskPlanner"""
    
    if not smart_client:
        raise HTTPException(status_code=503, detail="SmartLLMClient not available")
    
    try:
        config = request.config or {}
        config["task_id"] = request.task_id
        
        plan = await smart_client.generate_plan(request.prompt, config)
        
        logger.info(f"Generated plan for task {request.task_id}")
        
        return {
            "status": "success",
            "plan": plan,
            "task_id": request.task_id
        }
        
    except Exception as e:
        logger.error(f"Plan generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MANDAS Agent Worker",
        "version": "1.3.0",
        "status": "running",
        "endpoints": ["/health", "/test", "/plan"]
    }


if __name__ == "__main__":
    uvicorn.run("app.main_v13:app", host="0.0.0.0", port=8002, reload=True)
