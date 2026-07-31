from datetime import datetime
from typing import Literal, Optional

from sqlmodel import SQLModel

StoreStatus = Literal["draft", "published"]


class StoreCreate(SQLModel):
    owner_id: int
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    city: Optional[str] = "Barranquilla"


class StoreUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    city: Optional[str] = None
    status: Optional[StoreStatus] = None


class StoreResponse(SQLModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    logo_url: Optional[str]
    city: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
