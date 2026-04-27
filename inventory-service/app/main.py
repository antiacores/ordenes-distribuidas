import json
import pika
from app.db import SessionLocal, init_db
from app.models import Product
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

def get_connection():
    params = pika.URLParameters(RABBITMQ_URL)
    return pika.BlockingConnection(params)

def publish_event(channel, routing_key: str, event: dict):
    channel.basic_publish(
        exchange="orders",
        routing_key=routing_key,
        body=json.dumps(event).encode(),
        properties=pika.BasicProperties(delivery_mode=2),
    )

def handle_order(ch, method, properties, body):
    event = json.loads(body)
    order_id = event.get("order_id")
    items = event.get("items", [])

    print(f"[inventory] Verificando stock para orden {order_id}")

    db = SessionLocal()
    try:
        # Verificar stock
        for item in items:
            product = db.query(Product).filter(Product.sku == item["sku"]).first()

            if not product or product.stock < item["qty"]:
                print(f"[inventory] Stock insuficiente para SKU {item['sku']}")

                publish_event(ch, "order.stock_rejected", {
                    "order_id": order_id,
                    "reason": f"Stock insuficiente para SKU {item['sku']}"
                })

                ch.basic_ack(delivery_tag=method.delivery_tag)  
                return

        # Descontar stock
        for item in items:
            product = db.query(Product).filter(Product.sku == item["sku"]).first()
            product.stock -= item["qty"]

        db.commit()

        print(f"[inventory] Stock descontado para orden {order_id}")

        publish_event(ch, "order.stock_confirmed", {
            "order_id": order_id
        })

        ch.basic_ack(delivery_tag=method.delivery_tag) 

    except Exception as e:
        print("Error en inventory:", e)

        db.rollback()

        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)  

def main():
    print("inventory-service arrancando...")
    init_db()

    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange="orders", exchange_type="topic", durable=True)
    channel.queue_declare(queue="inventory_queue", durable=True)
    channel.queue_bind(exchange="orders", queue="inventory_queue", routing_key="order.created")

    print("Escuchando eventos de órdenes...")
    channel.basic_consume(queue="inventory_queue", on_message_callback=handle_order, auto_ack=False)
    channel.start_consuming()

if __name__ == "__main__":
    main()