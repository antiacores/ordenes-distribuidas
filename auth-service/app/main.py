from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, Header
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings
from app.db import SessionLocal, init_db
from app.models import Users
from app.schemas import UserRegister, AdminRegister, UserLogin, TokenResponse
from contextlib import asynccontextmanager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


@app.post("/auth/signup")
def signup(body: UserRegister):
    db = SessionLocal()
    try:
        if db.query(Users).filter(Users.email == body.email).first():
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        if db.query(Users).filter(Users.username == body.username).first():
            raise HTTPException(status_code=400, detail="El username ya está en uso")

        user = Users(
            email=body.email,
            username=body.username,
            name=body.name,
            password=pwd_context.hash(body.password),
        )
        db.add(user)
        db.commit()
        return {"message": "Usuario registrado exitosamente"}
    finally:
        db.close()


@app.post("/auth/signup/admin")
def signup_admin(body: AdminRegister, authorization: str = Header(...)):
    # Verificar que quien hace la petición es admin
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=403, detail="Solo un admin puede crear otros admins"
            )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    db = SessionLocal()
    try:
        if db.query(Users).filter(Users.email == body.email).first():
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        if db.query(Users).filter(Users.username == body.username).first():
            raise HTTPException(status_code=400, detail="El username ya está en uso")

        user = Users(
            email=body.email,
            username=body.username,
            name=body.name,
            password=pwd_context.hash(body.password),
            role="admin",
        )
        db.add(user)
        db.commit()
        return {"message": "Admin creado exitosamente"}
    finally:
        db.close()


@app.post("/auth/login", response_model=TokenResponse)
def login(body: UserLogin):
    db = SessionLocal()
    try:
        user = db.query(Users).filter(Users.email == body.email).first()
        if not user or not pwd_context.verify(body.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        access_token = create_token(
            {"sub": user.email, "username": user.username, "role": user.role},
            timedelta(minutes=settings.jwt_expire_minutes),
        )
        refresh_token = create_token(
            {"sub": user.email, "type": "refresh", "role": user.role},
            timedelta(days=settings.jwt_refresh_expire_days),
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    finally:
        db.close()


@app.post("/auth/refresh", response_model=TokenResponse)
def refresh(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    db = SessionLocal()
    try:
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        access_token = create_token(
            {"sub": user.email, "username": user.username, "role": user.role},
            timedelta(minutes=settings.jwt_expire_minutes),
        )
        refresh_token = create_token(
            {"sub": user.email, "type": "refresh", "role": user.role},
            timedelta(days=settings.jwt_refresh_expire_days),
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    finally:
        db.close()


# TODO: Implementar blacklist de tokens para logout real
@app.post("/auth/logout")
def logout():
    return {"message": "Sesión cerrada"}


@app.get("/auth/{token}")
def validate_token(token: str):
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return {
            "valid": True,
            "email": payload.get("sub"),
            "username": payload.get("username"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
