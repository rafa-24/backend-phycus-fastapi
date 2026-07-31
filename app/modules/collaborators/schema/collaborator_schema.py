from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class CollaboratorCreate(SQLModel):
    store_id: int
    full_name: str
    email: Optional[str] = None
    role: str = "staff"
    is_active: bool = True


class CollaboratorUpdate(SQLModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class CollaboratorResponse(SQLModel):
    id: int
    store_id: int
    user_id: int | None
    full_name: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
