from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class PaymentConfigCreate(SQLModel):
    store_id: int
    identity_key_bold: Optional[str] = None
    secret_key_bold: Optional[str] = None
    mode: Optional[str] = None
    color_button: Optional[str] = None
    size_button: Optional[str] = None
    redirect_url: Optional[str] = None


class PaymentConfigUpdate(SQLModel):
    identity_key_bold: Optional[str] = None
    secret_key_bold: Optional[str] = None
    mode: Optional[str] = None
    color_button: Optional[str] = None
    size_button: Optional[str] = None
    redirect_url: Optional[str] = None


class PaymentConfigResponse(SQLModel):
    id: int
    store_id: int
    identity_key_bold: Optional[str]
    mode: Optional[str]
    color_button: Optional[str]
    size_button: Optional[str]
    redirect_url: Optional[str]
    created_at: datetime


class BoldIntegrityRequest(SQLModel):
    order_id: str
    amount: int
    currency: str = "COP"


class BoldIntegrityResponse(SQLModel):
    order_id: str
    amount: int
    currency: str
    integrity_signature: str
