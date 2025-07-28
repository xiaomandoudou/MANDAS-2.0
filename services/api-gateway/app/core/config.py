from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://mandas:mandas123@localhost:5432/mandas"
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
    allowed_file_types: str = ".pdf,.txt,.md,.doc,.docx"
    
    @field_validator('allowed_file_types')
    @classmethod
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"


settings = Settings()
