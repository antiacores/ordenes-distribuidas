import asyncio
import json
import aio_pika
from app.config import settings

async def handle_order(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        order_id = event.get("order_id")
        items = event.get("items", [])

        print(f"[inventory] Descontando stock para orden {order_id}")
        for item in items:
            print(f"   - SKU: {item['sku']} | Cantidad: {item['qty']}")
    
async def main():
    print("inventory-service iniciado...")
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue("inventory_queue", durable=True)
    await queue.bind(exchange)

    print("Monitoreando eventos de órdenes...")
    await queue.consume(handle_order)
    await asyncio.Future()  # Mantener el servicio corriendo

if __name__ == "__main__":
    asyncio.run(main())