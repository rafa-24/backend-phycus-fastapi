from datetime import UTC, datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class PaymentDetail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="stores.id", index=True)
    identity_key_bold: Optional[str] = Field(default=None)
    secret_key_bold: Optional[str] = Field(default=None)
    mode: Optional[str] = Field(default=None)
    color_button: Optional[str] = Field(default=None)
    size_button: Optional[str] = Field(default=None)
    redirect_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))