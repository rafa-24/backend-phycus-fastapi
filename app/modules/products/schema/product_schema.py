from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class ProductCreate(SQLModel):
    store_id: int
    category_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: Decimal
    image_url: Optional[str] = None
    is_active: bool = True
    stock: Optional[int] = None
    discount_activate: Optional[bool] = None


class ProductUpdate(SQLModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    stock: Optional[int] = None
    discount_activate: Optional[bool] = None


class ProductResponse(SQLModel):
    id: int
    store_id: int
    category_id: Optional[int]
    name: str
    description: Optional[str]
    price: Decimal
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    stock: Optional[int] = None
    discount_activate: Optional[bool] = None


class ProductImportSkippedRow(SQLModel):
    row_number: int
    reason: str
    categoria: Optional[str] = None
    nombre: Optional[str] = None


class ProductImportResponse(SQLModel):
    products_created: int
    categories_created: int
    rows_skipped: int
    skipped_rows: list[ProductImportSkippedRow]
    products: list[ProductResponse]
