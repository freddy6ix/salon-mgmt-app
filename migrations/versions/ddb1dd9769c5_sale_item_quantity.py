"""sale_item_quantity

Revision ID: ddb1dd9769c5
Revises: 7f98b2ce8bb9
Create Date: 2026-04-28 22:24:51.789523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ddb1dd9769c5'
down_revision: Union[str, None] = '7f98b2ce8bb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sale_items',
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
    )


def downgrade() -> None:
    op.drop_column('sale_items', 'quantity')
