from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger
import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis
from app.core.logging import setup_logging
from app.core.tracing import setup_tracing
from app.api.v1 import tasks, documents, auth, health, tools, memory
from app.core.auth import verify_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    setup_tracing()
    await init_db()
    await init_redis()
    logger.info("Mandas API Gateway started successfully")
    yield
    logger.info("Mandas API Gateway shutting down")


app = FastAPI(
    title="Mandas Modular Agent System - API Gateway",
    description="脊椎 (Spine) - 任务调度中心 API Gateway",
    version="0.6.0",
    openapi_url="/mandas/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/mandas/v1/auth", tags=["auth"])
app.include_router(
    tasks.router, 
    prefix="/mandas/v1/tasks", 
    tags=["tasks"]
)
app.include_router(
    documents.router, 
    prefix="/mandas/v1/documents", 
    tags=["documents"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    tools.router,
    prefix="/mandas/v1/tools",
    tags=["tools"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    memory.router,
    prefix="/mandas/v1/memory", 
    tags=["memory"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    tasks.router,
    prefix="/internal",
    tags=["internal"],
    include_in_schema=False
)


@app.get("/")
async def root():
    return {
        "message": "Mandas Modular Agent System - API Gateway",
        "version": "0.6.0",
        "description": "脊椎 (Spine) - 任务调度中心",
        "status": "running"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
