from typing import Optional

from sqlmodel import SQLModel


class UserCreate(SQLModel):
    email: str
    password: str
    first_name: str
    last_name: Optional[str] = None
    cellphone: Optional[str] = None


class RoleResponse(SQLModel):
    id: int
    name: str


class UserResponse(SQLModel):
    id: int
    email: str
    first_name: str
    last_name: Optional[str] = None
    cellphone: Optional[str] = None
    role_id: int
    role: Optional[RoleResponse] = None
