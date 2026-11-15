from pydantic import BaseModel


class PayRequest(BaseModel):
    order_id: int


class PayResponse(BaseModel):
    order_id: int
    status: str
    message: str
