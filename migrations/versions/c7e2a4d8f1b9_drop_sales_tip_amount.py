"""Drop sales.tip_amount (P2-9: tips aren't salon revenue)

Revision ID: c7e2a4d8f1b9
Revises: b5d1e3f7c92a
Create Date: 2026-04-26

Salon Lyol's actual flow: client over-tenders, cashier returns the
overage as cashback to the client, who passes it to the staff member.
The tip never enters the salon's books or till. Drop the column.
"""
from alembic import op
import sqlalchemy as sa


revision = 'c7e2a4d8f1b9'
down_revision = 'b5d1e3f7c92a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('sales', 'tip_amount')


def downgrade() -> None:
    op.add_column(
        'sales',
        sa.Column('tip_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
    )
