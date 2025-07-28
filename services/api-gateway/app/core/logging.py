import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    logger.remove()
    
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    logger.add(
        "/app/logs/api-gateway.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="gz"
    )
    
    logger.add(
        "/app/logs/api-gateway-json.log",
        format=lambda record: f'{{"timestamp": "{record["time"]}", "level": "{record["level"].name}", "module": "{record["name"]}", "function": "{record["function"]}", "line": {record["line"]}, "message": "{record["message"]}"}}',
        level=settings.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="gz"
    )
    
    logger.info("Logging setup completed")
