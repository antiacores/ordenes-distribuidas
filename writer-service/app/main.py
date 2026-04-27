import asyncio
import json
from datetime import datetime, timezone
import aio_pika
from app.config import settings
from app.db import engine, Base, AsyncSessionLocal
from app.redis_client import r
from app.repositories.orders_repo import insert_order

async def handle_order_created(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        order_id = event.get("order_id")
        try:
            async with AsyncSessionLocal() as db:
                await insert_order(
                    db,
                    order_id=order_id,
                    customer=event.get("customer"),
                    items=event.get("items"),
                )
            print(f"Orden {order_id} persistida")
        except Exception as e:
            await r.hset(f"order:{order_id}", mapping={
                "status": "FAILED",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            })
            print(f"Error persistiendo orden {order_id}: {e}")

async def handle_stock_response(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        order_id = event.get("order_id")
        routing_key = message.routing_key

        if routing_key == "order.stock_confirmed":
            await r.hset(f"order:{order_id}", mapping={
                "status": "CONFIRMED",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            })
            print(f"Stock confirmado para orden {order_id}")
        elif routing_key == "order.stock_rejected":
            await r.hset(f"order:{order_id}", mapping={
                "status": "REJECTED",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            })
            print(f"Stock rechazado para orden {order_id}")

async def main():
    print("writer-service arrancando...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.TOPIC, durable=True)

    queue_created = await channel.declare_queue("writer_order_created", durable=True)
    await queue_created.bind(exchange, routing_key="order.created")
    await queue_created.consume(handle_order_created)

    queue_stock = await channel.declare_queue("writer_stock_response", durable=True)
    await queue_stock.bind(exchange, routing_key="order.stock_confirmed")
    await queue_stock.bind(exchange, routing_key="order.stock_rejected")
    await queue_stock.consume(handle_stock_response)

    print("Escuchando eventos...")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())