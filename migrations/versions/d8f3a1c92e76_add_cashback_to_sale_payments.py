"""Add cashback_amount to sale_payments (P2-9 v2)

Revision ID: d8f3a1c92e76
Revises: c7e2a4d8f1b9
Create Date: 2026-04-26

A payment line's cashback_amount is cash returned to the client out of
the till. The amount that counts toward the sale's bill is
(amount - cashback_amount). Used for both card-tip-via-cashback (the
common case at Salon Lyol) and cash change-making.
"""
from alembic import op
import sqlalchemy as sa


revision = 'd8f3a1c92e76'
down_revision = 'c7e2a4d8f1b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'sale_payments',
        sa.Column('cashback_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('sale_payments', 'cashback_amount')
