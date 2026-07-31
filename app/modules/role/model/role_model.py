from typing import List
from datetime import datetime, UTC
from sqlmodel import Field, SQLModel, Relationship


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(
        min_length=3,
        max_length=24
    )

    users: List["Users"] = Relationship(back_populates="role")

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))