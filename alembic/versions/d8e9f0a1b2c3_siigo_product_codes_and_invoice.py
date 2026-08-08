"""siigo product codes, ean and order invoice fields

Revision ID: d8e9f0a1b2c3
Revises: 705d4fa02ffa
Create Date: 2026-08-06 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
import sqlmodel


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "705d4fa02ffa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    columns = {col["name"] for col in inspect(bind).get_columns(table)}
    return column in columns


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    indexes = {idx["name"] for idx in inspect(bind).get_indexes(table)}
    return index_name in indexes


def upgrade() -> None:
    if not _has_column("products", "siigo_id"):
        op.add_column(
            "products",
            sa.Column(
                "siigo_id",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                nullable=True,
            ),
        )
    if not _has_column("products", "siigo_code"):
        op.add_column(
            "products",
            sa.Column(
                "siigo_code",
                sqlmodel.sql.sqltypes.AutoString(length=60),
                nullable=True,
            ),
        )
    if not _has_column("products", "ean"):
        op.add_column(
            "products",
            sa.Column(
                "ean",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                nullable=True,
            ),
        )
    if not _has_index("products", "ix_products_siigo_id"):
        op.create_index("ix_products_siigo_id", "products", ["siigo_id"])
    if not _has_index("products", "ix_products_siigo_code"):
        op.create_index("ix_products_siigo_code", "products", ["siigo_code"])

    if not _has_column("orders", "siigo_invoice_id"):
        op.add_column(
            "orders",
            sa.Column(
                "siigo_invoice_id",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                nullable=True,
            ),
        )
    if not _has_column("orders", "siigo_invoice_name"):
        op.add_column(
            "orders",
            sa.Column(
                "siigo_invoice_name",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                nullable=True,
            ),
        )


def downgrade() -> None:
    if _has_column("orders", "siigo_invoice_name"):
        op.drop_column("orders", "siigo_invoice_name")
    if _has_column("orders", "siigo_invoice_id"):
        op.drop_column("orders", "siigo_invoice_id")
    if _has_index("products", "ix_products_siigo_code"):
        op.drop_index("ix_products_siigo_code", table_name="products")
    if _has_index("products", "ix_products_siigo_id"):
        op.drop_index("ix_products_siigo_id", table_name="products")
    if _has_column("products", "ean"):
        op.drop_column("products", "ean")
    if _has_column("products", "siigo_code"):
        op.drop_column("products", "siigo_code")
    if _has_column("products", "siigo_id"):
        op.drop_column("products", "siigo_id")
