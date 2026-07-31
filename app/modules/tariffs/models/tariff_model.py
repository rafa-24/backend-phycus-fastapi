from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Tariffs(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="stores.id", index=True)
    localidad: str = Field(min_length=1, max_length=120)
    barrio: str = Field(min_length=1, max_length=180)
    tarifa: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    tarifa_enrutar: Optional[Decimal] = Field(
        default=None, max_digits=12, decimal_places=2
    )
    lat: Optional[float] = Field(default=None)
    lng: Optional[float] = Field(default=None)
    city: str = Field(default="Barranquilla", max_length=120)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
