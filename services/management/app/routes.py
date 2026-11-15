import os
import asyncio
import secrets
import string
import logging
from typing import List
from datetime import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Server
from app.schemas import ServerResponse, ActionResponse

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_password(length=12):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


async def get_user_server(server_id: int, user_id: int, db: AsyncSession) -> Server:
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if server.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your server")
    return server


@router.get("/api/servers/", response_model=List[ServerResponse])
async def list_servers(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    result = await db.execute(select(Server).where(Server.user_id == user_id))
    servers = result.scalars().all()
    return [ServerResponse.model_validate(s) for s in servers]


@router.post("/api/servers/{server_id}/reboot", response_model=ActionResponse)
async def reboot_server(
    server_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    server = await get_user_server(server_id, user_id, db)

    server.status = "restarting"
    server.updated_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Server {server_id} rebooting...")

    await asyncio.sleep(2)

    server.status = "active"
    server.updated_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Server {server_id} reboot complete")

    return ActionResponse(server_id=server_id, action="reboot", status="active", message="Server rebooted successfully")


@router.post("/api/servers/{server_id}/stop", response_model=ActionResponse)
async def stop_server(
    server_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    server = await get_user_server(server_id, user_id, db)

    server.status = "stopped"
    server.updated_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Server {server_id} stopped")

    return ActionResponse(server_id=server_id, action="stop", status="stopped", message="Server stopped")


@router.post("/api/servers/{server_id}/start", response_model=ActionResponse)
async def start_server(
    server_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    server = await get_user_server(server_id, user_id, db)

    server.status = "active"
    server.updated_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Server {server_id} started")

    return ActionResponse(server_id=server_id, action="start", status="active", message="Server started")


@router.post("/api/servers/{server_id}/reset-password", response_model=ActionResponse)
async def reset_password(
    server_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    server = await get_user_server(server_id, user_id, db)

    new_password = generate_password()
    server.root_password = new_password
    server.updated_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Server {server_id} password reset")

    return ActionResponse(
        server_id=server_id,
        action="reset-password",
        status=server.status,
        message=f"Password reset. New password: {new_password}",
    )
