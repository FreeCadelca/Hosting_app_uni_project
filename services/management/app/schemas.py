from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ServerResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    root_password: Optional[str] = None
    os: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ActionResponse(BaseModel):
    server_id: int
    action: str
    status: str
    message: str
