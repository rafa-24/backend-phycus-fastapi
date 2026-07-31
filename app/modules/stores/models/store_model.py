from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Stores(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default="Barranquilla", max_length=120)
    status: str = Field(default="draft", max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
