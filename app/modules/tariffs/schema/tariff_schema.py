from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class TariffCreate(SQLModel):
    store_id: int
    localidad: str
    barrio: str
    tarifa: Optional[Decimal] = None
    tarifa_enrutar: Optional[Decimal] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    city: Optional[str] = None
    is_active: bool = True


class TariffUpdate(SQLModel):
    localidad: Optional[str] = None
    barrio: Optional[str] = None
    tarifa: Optional[Decimal] = None
    tarifa_enrutar: Optional[Decimal] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    city: Optional[str] = None
    is_active: Optional[bool] = None


class TariffResponse(SQLModel):
    id: int
    store_id: int
    localidad: str
    barrio: str
    tarifa: Optional[Decimal]
    tarifa_enrutar: Optional[Decimal]
    lat: Optional[float]
    lng: Optional[float]
    city: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TariffImportSkippedRow(SQLModel):
    row_number: int
    reason: str
    localidad: Optional[str] = None
    barrio: Optional[str] = None


class TariffImportResponse(SQLModel):
    tariffs_created: int
    tariffs_updated: int
    rows_skipped: int
    skipped_rows: list[TariffImportSkippedRow]
    tariffs: list[TariffResponse]
