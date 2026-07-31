from typing import Optional

from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, UTC

from app.modules.role.model.role_model import Role

class Users(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = Field(index=True, min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=255)
    first_name: str = Field(index=True, min_length=3, max_length=50)
    last_name: str | None = Field(default= None, index=True, min_length=3, max_length=50)

    cellphone: str | None = Field(
        default= None,
        index=True, 
        min_length=3, 
        max_length=50
    )
    password_recovery_code: Optional[int] = Field(default=None)

    # clave foranea
    role_id: int = Field(foreign_key="roles.id")

    # relacion
    role: Optional[Role] = Relationship(back_populates= "users")

    # campos actualizados por registro
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
