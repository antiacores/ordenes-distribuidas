import json
import pika
import os
import time
import random

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

processed_orders = set()


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


def process_payment(order_id):
    print(f"[payments] START payment | order_id={order_id}")

    time.sleep(1)

    if random.random() < 0.2:
        print(f"[payments] PAGO FALLIDO | order_id={order_id}")
        return False

    print(f"[payments] PAGO EXITOSO | order_id={order_id}")
    return True


def handle_message(ch, method, properties, body):
    try:
        event = json.loads(body)
        order_id = event.get("order_id")

        print(f"[payments] Evento recibido: {method.routing_key}")
        print(f"[payments] Body recibido: {event}")

        if order_id in processed_orders:
            print(f"[payments] Ya procesado | order_id={order_id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if method.routing_key == "order.stock_confirmed":
            success = process_payment(order_id)

            if success:
                publish_event(
                    ch, "order.paid", {"order_id": order_id, "status": "paid"}
                )
            else:
                publish_event(
                    ch,
                    "order.payment_failed",
                    {"order_id": order_id, "status": "failed"},
                )

            processed_orders.add(order_id)

    except Exception as e:
        print(f"[payments] Error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    print("payments-service arrancando...")

    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange="orders", exchange_type="topic", durable=True)

    channel.queue_declare(queue="payments_queue", durable=True)

    channel.queue_bind(
        exchange="orders", queue="payments_queue", routing_key="order.stock_confirmed"
    )

    print("Escuchando eventos de pagos...")

    channel.basic_consume(
        queue="payments_queue", on_message_callback=handle_message, auto_ack=False
    )

    channel.start_consuming()


if __name__ == "__main__":
    main()
