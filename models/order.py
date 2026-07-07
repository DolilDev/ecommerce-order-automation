from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, field_validator


class OrderItem(BaseModel):
    name: str
    qty: int
    price: float

    @field_validator("qty")
    @classmethod
    def qty_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("qty must be greater than 0")
        return v

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be non-negative")
        return v


class Order(BaseModel):
    order_id: str
    customer_name: str
    customer_email: EmailStr
    items: List[OrderItem]
    total: float
    currency: str = "USD"
    created_at: datetime

    @field_validator("items")
    @classmethod
    def items_must_not_be_empty(cls, v: List[OrderItem]) -> List[OrderItem]:
        if not v:
            raise ValueError("order must contain at least one item")
        return v

    def items_summary(self) -> str:
        return ", ".join(f"{item.qty}x {item.name}" for item in self.items)
