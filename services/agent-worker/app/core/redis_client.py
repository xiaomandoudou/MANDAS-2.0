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
        
        try:
            await redis_client.xgroup_create(
                settings.redis_task_stream,
                settings.redis_consumer_group,
                id="0",
                mkstream=True
            )
            logger.info(f"Created consumer group: {settings.redis_consumer_group}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {settings.redis_consumer_group} already exists")
            else:
                raise
                
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def get_redis() -> redis.Redis:
    return redis_client
