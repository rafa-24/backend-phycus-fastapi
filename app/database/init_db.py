from alembic.config import Config
from alembic import command
from sqlmodel import SQLModel

from app.database.database import engine
from app.database.models import (  # noqa: F401
    Role,
    Users,
    Stores,
    Categories,
    Products,
    Collaborators,
    Discounts,
    Tariffs,
)


def run_migrations() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


def create_db() -> None:
    SQLModel.metadata.create_all(engine)
    run_migrations()
    print("Base de datos actualizada correctamente.")
