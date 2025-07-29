import redis.asyncio as redis
from loguru import logger
from app.core.config import settings


redis_client: redis.Redis = None


async def init_redis():
    global redis_client
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def get_redis() -> redis.Redis:
    return redis_client


async def publish_task_to_queue(task_id: str, priority: int = 5):
    try:
        message = {
            "task_id": task_id,
            "priority": priority,
            "timestamp": str(int(time.time()))
        }
        
        await redis_client.xadd(
            settings.redis_task_stream,
            message,
            maxlen=10000
        )
        
        logger.info(f"Task {task_id} published to Redis Stream")
        return True
    except Exception as e:
        logger.error(f"Failed to publish task {task_id} to queue: {e}")
        return False


import time
