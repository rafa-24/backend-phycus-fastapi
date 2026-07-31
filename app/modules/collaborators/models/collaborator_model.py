from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Collaborators(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="stores.id", index=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    full_name: str = Field(min_length=1, max_length=255)
    email: Optional[str] = Field(default=None, max_length=100)
    role: str = Field(default="staff", max_length=50)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
