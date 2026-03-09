## POST /internal/orders

from datetime import datetime, timezone
from fastapi import FastAPI, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import InternalOrder
from app.db import engine, Base, AsyncSessionLocal
from app.redis_client import r
from app.repositories.orders_repo import insert_order

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/internal/orders")
async def internal_create_order(body: InternalOrder, x_request_id: str = Header(default = "")):
    try:
        async with AsyncSessionLocal() as db:
            await insert_order(
                db,
                order_id = body.order_id,
                customer = body.customer,
                items = [item.model_dump() for item in body.items],
            )
        await r.hset(f"order:{body.order_id}", mapping = {
            "status": "PERSISTED",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })

        return {"order_id": body.order_id, "status": "PERSISTED"}
    
    except Exception as e:
        await r.hset(f"order:{body.order_id}", mapping = {
            "status": "ERROR",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })
        raise e