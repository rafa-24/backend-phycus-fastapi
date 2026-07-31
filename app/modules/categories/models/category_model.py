from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Categories(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="stores.id", index=True)
    name: str = Field(min_length=1, max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
