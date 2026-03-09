## Llamada HTTP al writer (timeout + retry)

import httpx
from app.config import settings

# Enviar order con timeout y 1 retry ("True" con éxito y "False" con error)
async def send_to_writer(order_id: str, request_id: str, payload: dict) -> bool:
    url = f"{settings.writer_service_url}/internal/orders"
    headers = {"X-Request-ID": request_id}

    for attempt in range(settings.writer_max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout = settings.writer_timeout_seconds) as client:
                response = await client.post(url, json = payload, headers = headers)
                response.raise_for_status()
                return True
        except Exception:
            pass
    return False