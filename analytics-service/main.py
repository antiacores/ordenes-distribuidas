import asyncio
import json
from datetime import datetime, timezone
import aio_pika
from app.config import settings

metrics = {
    "total_orders": 0,
    "total_items": 0,
    "orders": []
}

async def handle_order(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        order_id = event.get("order_id")
        items = event.get("items", [])
        total_items = sum(item.get("qty", 0) for item in items)

        metrics["total_orders"] += 1
        metrics["total_items"] += total_items
        metrics["orders"].append({
            "order_id": order_id,
            "total_items": total_items,
            "regstered_at": datetime.now(timezone.utc).isoformat()
        })

        print(f"[analytics-service] Orden {order_id} registrada | Total órdenes: {metrics['total_orders']} | Total items: {metrics['total_items']}")

async def main():
    print("analytics-service iniciando...")
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue("analytics_queue", durable=True)
    await queue.bind(exchange)

    print("Monitoreando eventos de órdenes...")
    await queue.consume(handle_order)
    await asyncio.Future()  # Mantener el servicio corriendo

if __name__ == "__main__":
    asyncio.run(main())