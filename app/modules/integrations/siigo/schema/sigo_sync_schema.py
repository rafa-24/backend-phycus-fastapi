from typing import Optional

from sqlmodel import SQLModel

from app.modules.products.schema.product_schema import ProductResponse


class SiigoSyncSkippedItem(SQLModel):
    siigo_id: Optional[str] = None
    siigo_code: Optional[str] = None
    name: Optional[str] = None
    reason: str


class SiigoSyncProductsResponse(SQLModel):
    fetched: int
    created: int
    updated: int
    skipped: int
    skipped_items: list[SiigoSyncSkippedItem]
    products: list[ProductResponse]


class SiigoInvoiceResult(SQLModel):
    invoice_id: Optional[str] = None
    invoice_name: Optional[str] = None
    number: Optional[int] = None
