from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os

DATABASE_URL = os.getenv("NOTIFICATIONS_DATABASE_URL", "postgresql+psycopg2://orders_user:orders_pass@postgres-notifications:5433/notifications_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("Tabla notificaciones creada/verificada")