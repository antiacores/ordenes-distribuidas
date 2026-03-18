from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://orders_user:orders_pass@postgres:5432/orders_db"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"

settings = Settings()