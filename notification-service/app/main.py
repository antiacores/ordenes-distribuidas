import json
import smtplib
import pika
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.db import SessionLocal, init_db
from app.models import Notification
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")

def get_connection():
    params = pika.URLParameters(RABBITMQ_URL)
    return pika.BlockingConnection(params)

def send_email(to: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, to, msg.as_string())

def save_notification(order_id: str, customer: str, event_type: str, message: str, reason: str = None):
    db = SessionLocal()
    try:
        notification = Notification(
            order_id=order_id,
            customer=customer,
            event_type=event_type,
            message=message,
            reason=reason,
        )
        db.add(notification)
        db.commit()
        print(f"[notification] Notificación guardada para orden {order_id}")
    except Exception as e:
        db.rollback()
        print(f"[notification] Error guardando notificación: {e}")
    finally:
        db.close()

def handle_message(ch, method, properties, body):
    event = json.loads(body)
    order_id = event.get("order_id")
    customer = event.get("customer", SMTP_USER)
    routing_key = method.routing_key

    print(f"[notification] Evento recibido: {routing_key} para orden {order_id}")

    if routing_key == "order.stock_confirmed":
        subject = f"Orden {order_id} confirmada"
        message = f"Hola,\n\nTu orden {order_id} fue confirmada y el stock fue reservado.\n\nGracias por tu compra :)"
        save_notification(order_id, customer, "stock_confirmed", message)

    elif routing_key == "order.stock_rejected":
        reason = event.get("reason", "Stock insuficiente")
        subject = f"Orden {order_id} rechazada"
        message = f"Hola,\n\nLo sentimos, tu orden {order_id} fue rechazada.\n\nMotivo: {reason}\n\nIntenta de nuevo más tarde."
        save_notification(order_id, customer, "stock_rejected", message, reason)

    try:
        send_email(SMTP_USER, subject, message)
        print(f"[notification] Correo enviado para orden {order_id}")
    except Exception as e:
        print(f"[notification] Error enviando correo: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print("notification-service arrancando...")
    init_db()

    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange="orders", exchange_type="topic", durable=True)
    channel.queue_declare(queue="notification_queue", durable=True)
    channel.queue_bind(exchange="orders", queue="notification_queue", routing_key="order.stock_confirmed")
    channel.queue_bind(exchange="orders", queue="notification_queue", routing_key="order.stock_rejected")

    print("Escuchando eventos...")
    channel.basic_consume(queue="notification_queue", on_message_callback=handle_message, auto_ack=False)
    channel.start_consuming()

if __name__ == "__main__":
    main()