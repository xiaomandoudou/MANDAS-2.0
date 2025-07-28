from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql://mandas:mandas123@localhost:5432/mandas"
    redis_url: str = "redis://localhost:6379"
    chromadb_url: str = "http://localhost:8000"
    ollama_url: str = "http://localhost:11434"
    
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    log_level: str = "INFO"
    
    redis_task_queue: str = "mandas:tasks:queue"
    redis_task_stream: str = "mandas:tasks:stream"
    
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: list[str] = [".pdf", ".txt", ".md", ".doc", ".docx"]
    
    class Config:
        env_file = ".env"


settings = Settings()
