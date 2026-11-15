from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class Credentials(BaseModel):
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not 8 <= len(value.encode()) <= 72:
            raise ValueError("Password must contain 8 to 72 UTF-8 bytes")
        return value


class UserRegister(Credentials):
    email: str
    password: str


class UserLogin(Credentials):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
