from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    auth_database_url: str = "postgresql+psycopg2://orders_user:orders_pass@postgres-auth:5432/auth_db"
    jwt_secret: str = ""
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

settings = Settings()