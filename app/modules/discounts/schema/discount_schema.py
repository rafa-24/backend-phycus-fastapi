from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from sqlmodel import SQLModel

DiscountType = Literal["promotion", "coupon"]


class DiscountCreate(SQLModel):
    store_id: int
    product_id: Optional[int] = None
    type: DiscountType
    name: str
    code: Optional[str] = None
    discount_percent: Decimal
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: bool = True


class DiscountUpdate(SQLModel):
    product_id: Optional[int] = None
    type: Optional[DiscountType] = None
    name: Optional[str] = None
    code: Optional[str] = None
    discount_percent: Optional[Decimal] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class DiscountResponse(SQLModel):
    id: int
    store_id: int
    product_id: Optional[int]
    type: str
    name: str
    code: Optional[str]
    discount_percent: Decimal
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    is_active: bool
    created_at: datetime
