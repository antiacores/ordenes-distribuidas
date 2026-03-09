## POST /orders, GET /orders/{id}

import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from app.schemas import CreateOrderRequest
from app.redis_client import r
from app.services.writer_client import send_to_writer

app = FastAPI()

@app.post("/orders")
async def create_order(body: CreateOrderRequest):
    order_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await r.hset(f"order:{order_id}", mapping = {
        "status": "RECEIVED", 
        "last_updated": now,
        })
    
    payload = {
        "order_id": order_id,
        "customer": body.customer,
        "items": [items.model_dump() for items in body.items],
    }

    success = await send_to_writer(order_id, request_id, payload)

    if not success:
        await r.hset(f"order:{order_id}", mapping = {
            "status": "FAILED",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })

    return {"order_id": order_id, "status": "RECEIVED"}

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    data = await r.hgetall(f"order:{order_id}")

    if not data:
        raise HTTPException(status_code = 404, detail = "Orden no encontrada")
    
    return {
        "order_id": order_id,
        "status": data.get("status"),
        "last_updated": data.get("last_updated"),
    }