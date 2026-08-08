"""tabla orders y order_items para pedidos Bold

Revision ID: a1b2c3d4e5f6
Revises: bcb4f8e92edc
Create Date: 2026-08-05 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "bcb4f8e92edc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("order_identifier", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=False),
        sa.Column("currency", sqlmodel.sql.sqltypes.AutoString(length=3), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("shipping_cost", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("integrity_signature", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=True),
        sa.Column("payment_status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("fulfillment_status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("customer_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("customer_phone", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=True),
        sa.Column("customer_email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("delivery_address", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("delivery_neighborhood", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("delivery_locality", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("delivery_city", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=True),
        sa.Column("tariff_id", sa.Integer(), nullable=True),
        sa.Column("bold_payment_id", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=True),
        sa.Column("bold_payment_method", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=True),
        sa.Column("bold_event_type", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_orders_store_id"), ["store_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_orders_order_identifier"),
            ["order_identifier"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_orders_payment_status"),
            ["payment_status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_orders_fulfillment_status"),
            ["fulfillment_status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_orders_bold_payment_id"),
            ["bold_payment_id"],
            unique=False,
        )

    op.create_table(
        "orderitems",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("product_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("product_image_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("orderitems", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_orderitems_order_id"), ["order_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("orderitems", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_orderitems_order_id"))
    op.drop_table("orderitems")

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_orders_bold_payment_id"))
        batch_op.drop_index(batch_op.f("ix_orders_fulfillment_status"))
        batch_op.drop_index(batch_op.f("ix_orders_payment_status"))
        batch_op.drop_index(batch_op.f("ix_orders_order_identifier"))
        batch_op.drop_index(batch_op.f("ix_orders_store_id"))
    op.drop_table("orders")
