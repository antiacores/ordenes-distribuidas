import asyncio
import json
from datetime import datetime, timezone
import aio_pika
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

metrics = {
    "total_orders": 0,
    "total_confirmed": 0,
    "total_rejected": 0,
    "total_items": 0,
    "orders": []
}

async def handle_event(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        order_id = event.get("order_id")
        routing_key = message.routing_key

        if routing_key == "order.created":
            items = event.get("items", [])
            total_items = sum(item.get("qty", 0) for item in items)
            metrics["total_orders"] += 1
            metrics["total_items"] += total_items
            metrics["orders"].append({
                "order_id": order_id,
                "total_items": total_items,
                "status": "created",
                "registered_at": datetime.now(timezone.utc).isoformat()
            })
            print(f"[analytics] Orden creada {order_id} | Total órdenes: {metrics['total_orders']} | Total items: {metrics['total_items']}")

        elif routing_key == "order.stock_confirmed":
            metrics["total_confirmed"] += 1
            for order in metrics["orders"]:
                if order["order_id"] == order_id:
                    order["status"] = "confirmed"
            print(f"[analytics] Orden confirmada {order_id} | Total confirmadas: {metrics['total_confirmed']}")

        elif routing_key == "order.stock_rejected":
            metrics["total_rejected"] += 1
            for order in metrics["orders"]:
                if order["order_id"] == order_id:
                    order["status"] = "rejected"
            print(f"[analytics] Orden rechazada {order_id} | Total rechazadas: {metrics['total_rejected']}")

async def main():
    print("analytics-service arrancando...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue("analytics_queue", durable=True)
    await queue.bind(exchange, routing_key="order.created")
    await queue.bind(exchange, routing_key="order.stock_confirmed")
    await queue.bind(exchange, routing_key="order.stock_rejected")

    print("Escuchando eventos...")
    await queue.consume(handle_event)
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())