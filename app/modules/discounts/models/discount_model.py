from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Discounts(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="stores.id", index=True)
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    type: str = Field(max_length=20)  # promotion | coupon
    name: str = Field(min_length=1, max_length=255)
    code: Optional[str] = Field(default=None, max_length=50)
    discount_percent: Decimal = Field(max_digits=5, decimal_places=2)
    starts_at: Optional[datetime] = Field(default=None)
    ends_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
