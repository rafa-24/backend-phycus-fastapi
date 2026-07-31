"""initial_schema

Revision ID: 42790b6a8c9f
Revises: 
Create Date: 2026-07-27 15:34:19.567518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42790b6a8c9f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('collaborators', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_collaborators_user_id'), ['user_id'], unique=False
        )
        batch_op.create_foreign_key(
            'fk_collaborators_user_id_users',
            'users',
            ['user_id'],
            ['id'],
        )

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stock', sa.Integer(), nullable=True))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'password',
            existing_type=sa.VARCHAR(length=50),
            type_=sa.String(length=255),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'password',
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=50),
            existing_nullable=False,
        )

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('stock')

    with op.batch_alter_table('collaborators', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_collaborators_user_id_users', type_='foreignkey'
        )
        batch_op.drop_index(batch_op.f('ix_collaborators_user_id'))
