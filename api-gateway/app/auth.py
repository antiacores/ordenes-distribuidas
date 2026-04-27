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

async def verify_admin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Se requiere rol de admin")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
async def forward_auth(path: str, body: dict, headers: dict = None) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}{path}",
            json=body,
            headers=headers or {},
        )
        response.raise_for_status()
        return response.json()