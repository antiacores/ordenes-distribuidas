## Variables de entorno

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = "redis://redis:6379/0"
    writer_service_url: str = "http://writer-service:8001"
    writer_timeout_seconds: float = 1.0
    writer_max_retries: int = 1

settings = Settings()