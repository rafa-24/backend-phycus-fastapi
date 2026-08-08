from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class SigoDetailCreate(SQLModel):
    store_id: int
    user_api: str
    access_key: str


class SigoDetailUpdate(SQLModel):
    user_api: Optional[str] = None
    access_key: Optional[str] = None


class SigoDetailResponse(SQLModel):
    """Respuesta segura: no expone access_key ni access_token."""

    id: int
    store_id: int
    user_api: Optional[str] = None
    has_access_key: bool = False
    status_connection: Optional[bool] = None
    token_type: Optional[str] = None
    expiration_time: Optional[float] = None
    created_at: datetime
