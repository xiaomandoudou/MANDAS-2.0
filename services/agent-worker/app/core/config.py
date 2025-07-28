from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://mandas:mandas123@localhost:5432/mandas"
    redis_url: str = "redis://localhost:6379"
    chromadb_url: str = "http://localhost:8000"
    ollama_url: str = "http://localhost:11434"
    
    postgres_db: str = "mandas"
    postgres_user: str = "mandas"
    postgres_password: str = "mandas123"
    
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    
    log_level: str = "INFO"
    
    redis_task_stream: str = "mandas:tasks:stream"
    redis_consumer_group: str = "agent-workers"
    redis_consumer_name: str = "worker-1"
    
    docker_image_python: str = "python:3.11-slim"
    docker_image_ubuntu: str = "ubuntu:22.04"
    
    max_task_timeout: int = 3600  # 1 hour
    max_retry_count: int = 3
    max_agent_rounds: int = 20  # V0.6: GroupChat最大轮数
    
    tools_directory: str = "/app/tools.d"
    
    max_container_memory: str = "1g"
    max_container_cpu: float = 0.5
    container_timeout: int = 600
    
    short_term_memory_ttl: int = 3600  # 1小时
    max_short_term_messages: int = 50
    max_agent_rounds: int = 20  # V0.6: GroupChat最大轮数
    
    tools_directory: str = "/app/tools.d"
    
    max_container_memory: str = "1g"
    max_container_cpu: float = 0.5
    container_timeout: int = 600
    
    short_term_memory_ttl: int = 3600  # 1小时
    max_short_term_messages: int = 50
    
    class Config:
        env_file = ".env"


settings = Settings()
