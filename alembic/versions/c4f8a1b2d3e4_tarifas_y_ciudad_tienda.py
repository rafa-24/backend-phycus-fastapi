"""tarifas y ciudad en tienda

Revision ID: c4f8a1b2d3e4
Revises: b2294a386962
Create Date: 2026-07-16 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4f8a1b2d3e4"
down_revision: Union[str, Sequence[str], None] = "b2294a386962"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "stores" in tables:
        store_columns = {column["name"] for column in inspector.get_columns("stores")}
        if "city" not in store_columns:
            op.add_column(
                "stores",
                sa.Column(
                    "city",
                    sa.String(length=120),
                    nullable=True,
                    server_default="Barranquilla",
                ),
            )

    if "tariffs" not in tables:
        op.create_table(
            "tariffs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("localidad", sa.String(length=120), nullable=False),
            sa.Column("barrio", sa.String(length=180), nullable=False),
            sa.Column("tarifa", sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column(
                "tarifa_enrutar", sa.Numeric(precision=12, scale=2), nullable=True
            ),
            sa.Column("lat", sa.Float(), nullable=True),
            sa.Column("lng", sa.Float(), nullable=True),
            sa.Column(
                "city",
                sa.String(length=120),
                nullable=False,
                server_default="Barranquilla",
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            ),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_tariffs_store_id"), "tariffs", ["store_id"], unique=False
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "tariffs" in tables:
        op.drop_index(op.f("ix_tariffs_store_id"), table_name="tariffs")
        op.drop_table("tariffs")

    if "stores" in tables:
        store_columns = {column["name"] for column in inspector.get_columns("stores")}
        if "city" in store_columns:
            op.drop_column("stores", "city")
