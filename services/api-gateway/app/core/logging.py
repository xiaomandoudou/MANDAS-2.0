import sys
import os
import json
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
    
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger.add(
        os.path.join(log_dir, "api-gateway.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="gz"
    )
    
    logger.add(
        os.path.join(log_dir, "api-gateway-json.log"),
        format=lambda record: json.dumps({
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "trace_id": record["extra"].get("trace_id", ""),
            "request_id": record["extra"].get("request_id", ""),
            "user_id": record["extra"].get("user_id", ""),
            "span_id": record["extra"].get("span_id", "")
        }),
        level=settings.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="gz"
    )
    
    logger.info("Logging setup completed")
