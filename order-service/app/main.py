import asyncio
import json
from datetime import datetime
import aio_pika
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.config import settings

engine = create_async_engine(settings.database_url)
AsynSessionLocal = async_sessionmaker(engine)

# Guardar los order id ya publicados para no duplicar eventos
published = set()

async def get_new_orders():
    async with AsynSessionLocal() as db:
        result = await db.execute(text("SELECT order_id, customer, items, created_at FROM orders"))
        return result.fetchall()
    
async def main():
    print("order-service arrancando...")
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.FANOUT, durable=True)

    print("Monitoreando órdenes nuevas en Postgres...")
    while True:
        try:
            orders = await get_new_orders()
            for order in orders:
                order_id = order[0]
                if order_id not in published:
                    event = {
                        "order_id": order[0],
                        "customer": order[1],
                        "items": order[2],
                        "created_at": order[3].isoformat() if order[3] else datetime.now(timezone.utc).isoformat()
                    }
                    await exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(event).encode(),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key="",
                    )
                    published.add(order_id)
                    print(f"Evento publicado: {order_id}")
        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())