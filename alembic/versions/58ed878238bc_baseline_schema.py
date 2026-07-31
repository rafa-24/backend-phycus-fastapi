"""baseline_schema

Revision ID: 58ed878238bc
Revises: 42790b6a8c9f
Create Date: 2026-07-27 15:35:55.115837

"""

from typing import Sequence, Union


revision: str = "58ed878238bc"
down_revision: Union[str, Sequence[str], None] = "42790b6a8c9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
