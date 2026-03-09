## Variables de entorno

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://orders_user:orders_pass@postgres:5432/orders_db"
    redis_url: str = "redis://redis:6379/0"

settings = Settings()