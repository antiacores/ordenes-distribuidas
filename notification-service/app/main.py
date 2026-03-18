import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aio_pika
from app.config import settings

def send_email(to: str, order_id: str, items: list):
    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = f"Confirmación de orden - {order_id}"

    items_text = "\n".join([f"   - SKU {i['sku']} | Cantidad: {i['qty']}" for i in items])
    body = f"Hola,\n\nTu orden {order_id} fue recibida exitosamente. \n\nProductos:\n{items_text}\n\nGracias por tu compra :)"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, to, msg.as_string())

async def handle_order(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        order_id = event.get("order_id")
        customer = event.get("customer")
        items = event.get("items", [])

        print(f"[notification-service] Mandando correo para orden {order_id} a {customer}")
        try:
            send_email(settings.smtp_user, order_id, items)
            print(f"[notification-service] Correo enviado para orden {order_id}")
        except Exception as e:
            print(f"[notification-service] Error al enviar correo para orden: {e}")

async def main():
    print("notification-service iniciando...")
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue("notification_queue", durable=True)
    await queue.bind(exchange)

    print("Monitoreando eventos de órdenes...")
    await queue.consume(handle_order)
    await asyncio.Future()  # Mantener el servicio corriendo

if __name__ == "__main__":
    asyncio.run(main())