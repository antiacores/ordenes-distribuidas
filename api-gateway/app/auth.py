import httpx
from fastapi import HTTPException, Header
from jose import jwt, JWTError
import os

JWT_SECRET = os.getenv("JWT_SECRET", "")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8002")

async def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

async def forward_auth(path: str, body: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}{path}", json=body)
        response.raise_for_status()
        return response.json()