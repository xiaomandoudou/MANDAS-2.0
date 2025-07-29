from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
from app.core.database import get_db
from app.core.redis_client import get_redis
from loguru import logger

router = APIRouter()


@router.get("/mandas/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "mandas-api-gateway",
        "version": "0.6.0",
        "mandas_version": "v0.6"
    }


@router.get("/mandas/v1/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    health_status = {
        "status": "healthy",
        "service": "mandas-api-gateway",
        "version": "0.6.0",
        "mandas_version": "v0.6",
        "checks": {}
    }
    
    try:
        result = await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    try:
        await redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["checks"]["redis"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    return health_status
