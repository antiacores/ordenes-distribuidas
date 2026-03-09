## Modelo Pydantic (InternalOrder)

from pydantic import BaseModel
from typing import List

class OrderItem(BaseModel):
    sku: str
    qty: int

class InternalOrder(BaseModel):
    order_id: str
    customer: str
    items: List[OrderItem]