from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os
from urllib.parse import urlsplit, urlunsplit

def normalize_database_url(raw_url, driver="asyncpg"):
    normalized = raw_url.strip()

    if normalized.startswith("postgres://"):
        normalized = normalized.replace("postgres://", f"postgresql+{driver}://", 1)
    if normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", f"postgresql+{driver}://", 1)
    if normalized.startswith("postgresql+psycopg2://"):
        normalized = normalized.replace("postgresql+psycopg2://", f"postgresql+{driver}://", 1)
    if normalized.startswith("postgresql+asyncpg://"):
        normalized = normalized.replace("postgresql+asyncpg://", f"postgresql+{driver}://", 1)

    parts = urlsplit(normalized)
    db_name = parts.path.lstrip("/")

    # Handle common deploy typo: trailing unmatched brace in DB name (e.g. railway}).
    if db_name.endswith("}") and "{" not in db_name:
        cleaned_name = db_name.rstrip("}")
        normalized = urlunsplit(
            (parts.scheme, parts.netloc, f"/{cleaned_name}", parts.query, parts.fragment)
        )
        parts = urlsplit(normalized)
        db_name = parts.path.lstrip("/")

    if "${" in normalized or "{" in db_name or "}" in db_name:
        raise ValueError(
            "DATABASE_URL parece inválida o con placeholders sin resolver. "
            f"Valor recibido: {normalized}"
        )

    return normalized

DATABASE_URL = normalize_database_url(os.getenv("NOTIFICATIONS_DATABASE_URL", "postgresql://orders_user:orders_pass@postgres-notifications:5433/notifications_db"), "psycopg2")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("Tabla notificaciones creada/verificada")