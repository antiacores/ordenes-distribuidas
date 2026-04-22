import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import CreateOrderRequest
from app.redis_client import r
from app.rabbitmq_publisher import publish_order_created
from app.auth import verify_token, verify_admin, forward_auth

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/auth/signup")
async def signup(body: dict):
    return await forward_auth("/auth/signup", body)

@app.post("/auth/signup/admin")
async def signup_admin(body: dict, authorization: str = Header(...), payload: dict = Depends(verify_admin)):
    return await forward_auth("/auth/signup/admin", body, headers={"Authorization": authorization})

@app.post("/auth/login")
async def login(body: dict):
    return await forward_auth("/auth/login", body)

@app.post("/auth/refresh")
async def refresh(body: dict):
    return await forward_auth("/auth/refresh", body)

@app.post("/auth/logout")
async def logout(body: dict):
    return await forward_auth("/auth/logout", body)

@app.post("/orders", status_code=202)
async def create_order(body: CreateOrderRequest, payload: dict = Depends(verify_token)):
    order_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await r.hset(f"order:{order_id}", mapping={
        "status": "RECEIVED",
        "last_updated": now,
        "customer_email": payload.get("sub"),
    })

    event = {
        "order_id": order_id,
        "customer": body.customer,
        "items": [item.model_dump() for item in body.items],
    }

    await publish_order_created(event)
    return {"order_id": order_id, "status": "RECEIVED"}

@app.get("/orders")
async def get_all_orders(payload: dict = Depends(verify_admin)):
    # Buscar todas las keys de órdenes en Redis
    keys = await r.keys("order:*")
    orders = []
    for key in keys:
        data = await r.hgetall(key)
        order_id = key.replace("order:", "")
        orders.append({
            "order_id": order_id,
            "status": data.get("status"),
            "last_updated": data.get("last_updated"),
            "customer_email": data.get("customer_email"),
        })
    return {"orders": orders}

@app.get("/orders/{order_id}")
async def get_order(order_id: str, payload: dict = Depends(verify_token)):
    data = await r.hgetall(f"order:{order_id}")

    if not data:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    # Si es customer, solo puede ver sus propias órdenes
    if payload.get("role") == "customer":
        if data.get("customer_email") != payload.get("sub"):
            raise HTTPException(status_code=403, detail="No tienes permiso para ver esta orden")

    return {
        "order_id": order_id,
        "status": data.get("status"),
        "last_updated": data.get("last_updated"),
        "customer_email": data.get("customer_email"),
    }