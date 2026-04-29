"""Make audit user FK columns nullable to allow staff hard-delete

Revision ID: u5p9j4k2l8m6
Revises: t4o8i3j1k7l5
Create Date: 2026-04-29

"""
from alembic import op

revision = "u5p9j4k2l8m6"
down_revision = "t4o8i3j1k7l5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("appointments", "created_by_user_id", nullable=True)
    op.alter_column("sale_payment_edits", "edited_by_user_id", nullable=True)
    op.alter_column("petty_cash_entries", "created_by_user_id", nullable=True)
    op.alter_column("retail_stock_movements", "created_by_user_id", nullable=True)


def downgrade() -> None:
    op.alter_column("retail_stock_movements", "created_by_user_id", nullable=False)
    op.alter_column("petty_cash_entries", "created_by_user_id", nullable=False)
    op.alter_column("sale_payment_edits", "edited_by_user_id", nullable=False)
    op.alter_column("appointments", "created_by_user_id", nullable=False)
