from datetime import datetime

from sqlmodel import SQLModel


class CategoryCreate(SQLModel):
    store_id: int
    name: str


class CategoryUpdate(SQLModel):
    name: str | None = None


class CategoryResponse(SQLModel):
    id: int
    store_id: int
    name: str
    created_at: datetime
