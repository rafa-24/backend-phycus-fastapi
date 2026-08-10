#from alembic.config import Config
#from alembic import command
from sqlmodel import SQLModel
import sqlitecloud

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


"""
def run_migrations() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
"""

def create_db() -> None:
    try:
        SQLModel.metadata.create_all(engine)
        print("Tablas verificadas y creadas correctamente.")
    except Exception as e:
        print(f'Error al crear tablas: {e}')
