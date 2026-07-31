from sqlmodel import SQLModel


class RoleCreate(SQLModel):
    name: str
