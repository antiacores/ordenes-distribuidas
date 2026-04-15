## POST /orders, GET /orders/{id}

import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import CreateOrderRequest
from app.redis_client import r
from app.rabbitmq_publisher import publish_order_created

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/orders", status_code=202)
async def create_order(body: CreateOrderRequest):
    order_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await r.hset(f"order:{order_id}", mapping={
        "status": "RECEIVED",
        "last_updated": now,
    })

    event = {
        "order_id": order_id,
        "customer": body.customer,
        "items": [item.model_dump() for item in body.items],
    }

    await publish_order_created(event)

    return {"order_id": order_id, "status": "RECEIVED"}

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    data = await r.hgetall(f"order:{order_id}")

    if not data:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    return {
        "order_id": order_id,
        "status": data.get("status"),
        "last_updated": data.get("last_updated"),
    }