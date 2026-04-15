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

INVENTORY_DATABASE_URL = normalize_database_url(os.getenv("INVENTORY_DATABASE_URL", "postgresql://orders_user:orders_pass@postgres:5432/orders_db"), "psycopg2")

engine = create_engine(INVENTORY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        from app.models import Product
        if not db.query(Product).first():
            products = [
                Product(sku="CAM-BLN-M", name="Camisa blanca talla M", stock=50),
                Product(sku="CAM-BLN-L", name="Camisa blanca talla L", stock=40),
                Product(sku="PAN-NEG-32", name="Pantalón negro talla 32", stock=30),
                Product(sku="PAN-KAK-32", name="Pantalón kaki talla 32", stock=25),
                Product(sku="CHA-GRS-L", name="Chamarra gris talla L", stock=20),
                Product(sku="VES-ROJ-S", name="Vestido rojo talla S", stock=15),
                Product(sku="SUD-AZL-XL", name="Sudadera azul talla XL", stock=35),
                Product(sku="TEN-BLN-27", name="Tenis blancos talla 27", stock=45),
                Product(sku="ABR-BEI-M", name="Abrigo beige talla M", stock=10),
                Product(sku="BOT-CAF-37", name="Botas café talla 37", stock=12),
            ]
            db.add_all(products)
            db.commit()
            print("Productos inicializados")