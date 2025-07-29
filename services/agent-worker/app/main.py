import asyncio
import signal
import sys
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis
from app.core.logging.enhanced_logger import setup_logging
from app.core.tracing import setup_tracing
from app.worker.task_consumer import TaskConsumer


class AgentWorkerService:
    def __init__(self):
        self.task_consumer = None
        self.running = False

    async def start(self):
        setup_logging()
        setup_tracing()
        
        await init_db()
        await init_redis()
        
        self.task_consumer = TaskConsumer()
        await self.task_consumer.initialize()
        
        self.running = True
        logger.info("Mandas Agent Worker started successfully")
        
        try:
            await self.task_consumer.start_consuming()
        except Exception as e:
            logger.error(f"Error in task consumer: {e}")
            raise

    async def stop(self):
        logger.info("Shutting down Agent Worker...")
        self.running = False
        
        if self.task_consumer:
            await self.task_consumer.stop()
        
        logger.info("Agent Worker shutdown complete")

    def handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop())


async def main():
    service = AgentWorkerService()
    
    signal.signal(signal.SIGINT, service.handle_signal)
    signal.signal(signal.SIGTERM, service.handle_signal)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
