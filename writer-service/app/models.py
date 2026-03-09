## Modelo ORM (Order)

from datetime import datetime, timezone
from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(36), primary_key = True)
    customer: Mapped[str] = mapped_column(String(255), nullable = False)
    items: Mapped[dict] = mapped_column(JSON, nullable = False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
    )