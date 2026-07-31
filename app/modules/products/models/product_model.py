from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Products(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="stores.id", index=True)
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)
    price: Decimal = Field(max_digits=10, decimal_places=2)
    image_url: Optional[str] = Field(default=None, max_length=500) # Imagen generada con IA
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stock: int | None = Field(default=None, nullable=True)
    discount_activate: bool | None = Field(default=None, nullable=True)