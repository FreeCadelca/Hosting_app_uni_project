from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PlanResponse(BaseModel):
    id: int
    name: str
    cpu: int
    ram_mb: int
    disk_gb: int
    price_monthly: float

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    plan_id: int


class OrderResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    server_id: int
    amount: float
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
