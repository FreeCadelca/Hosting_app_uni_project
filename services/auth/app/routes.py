import os
import json
import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, UserResponse, TokenResponse

logger = logging.getLogger(__name__)
router = APIRouter()


security = HTTPBearer()

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

REDIS_URL = os.environ["REDIS_URL"]
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


def create_jwt_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return decode_jwt_token(credentials.credentials)


@router.post("/api/auth/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=data.email,
        password_hash=bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User registered: {user.email} (id={user.id})")

    token = create_jwt_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.post("/api/auth/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not bcrypt.checkpw(data.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    logger.info(f"User logged in: {user.email} (id={user.id})")

    # Cache user data in Redis
    user_data = {"id": user.id, "email": user.email, "created_at": str(user.created_at)}
    await redis_client.setex(f"user:{user.id}", 600, json.dumps(user_data))

    token = create_jwt_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.get("/api/auth/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]

    # Try Redis cache first
    cached = await redis_client.get(f"user:{user_id}")
    if cached:
        logger.info(f"User {user_id} data from Redis cache")
        data = json.loads(cached)
        return UserResponse(**data)

    # Fallback to DB
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cache for next time
    user_data = {"id": user.id, "email": user.email, "created_at": str(user.created_at)}
    await redis_client.setex(f"user:{user.id}", 600, json.dumps(user_data))

    return UserResponse.model_validate(user)
