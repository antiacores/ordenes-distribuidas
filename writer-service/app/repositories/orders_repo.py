## Insert idempotente

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Order

async def insert_order(db: AsyncSession, order_id: str, customer: str, items: list) -> bool:
    result = await db.execute(select(Order).where(Order.order_id == order_id))
    existing = result.scalar_one_or_none()

    if existing:
        return False
    
    order = Order(order_id = order_id, customer = customer, items = items)
    db.add(order)
    await db.commit()
    return True