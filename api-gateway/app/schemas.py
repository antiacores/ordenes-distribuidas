## Modelos Pydantic

from pydantic import BaseModel
from typing import List

class OrderItem(BaseModel):
    sku: str
    quantity: int

class CreateOrderRequest(BaseModel):
    customer: str
    items: List[OrderItem]