import os
import json
import logging
from typing import List

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.database import get_db
from app.models import Plan, Server, Order
from app.schemas import PlanResponse, OrderCreate, OrderResponse

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

REDIS_URL = os.environ["REDIS_URL"]
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/api/products/plans", response_model=List[PlanResponse])
async def get_plans(db: AsyncSession = Depends(get_db)):
    # Try Redis cache first
    cached = await redis_client.get("plans:all")
    if cached:
        logger.info("Plans served from Redis cache")
        plans_data = json.loads(cached)
        return [PlanResponse(**p) for p in plans_data]

    # Fetch from DB
    result = await db.execute(select(Plan))
    plans = result.scalars().all()

    # Cache in Redis (TTL 300 sec)
    plans_data = [
        {
            "id": p.id,
            "name": p.name,
            "cpu": p.cpu,
            "ram_mb": p.ram_mb,
            "disk_gb": p.disk_gb,
            "price_monthly": float(p.price_monthly),
        }
        for p in plans
    ]
    await redis_client.setex("plans:all", 300, json.dumps(plans_data))
    logger.info("Plans fetched from DB and cached in Redis")

    return [PlanResponse(**p) for p in plans_data]


@router.post("/api/products/order", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]

    # Get plan
    result = await db.execute(select(Plan).where(Plan.id == data.plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Create server record (pending)
    server = Server(
        user_id=user_id,
        plan_id=plan.id,
        status="pending",
    )
    db.add(server)
    await db.flush()

    # Create order
    order = Order(
        user_id=user_id,
        plan_id=plan.id,
        server_id=server.id,
        amount=float(plan.price_monthly),
        status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    logger.info(f"Order {order.id} created for user {user_id}, plan {plan.name}, server {server.id}")

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        plan_id=order.plan_id,
        server_id=order.server_id,
        amount=float(order.amount),
        status=order.status,
        created_at=order.created_at,
    )
