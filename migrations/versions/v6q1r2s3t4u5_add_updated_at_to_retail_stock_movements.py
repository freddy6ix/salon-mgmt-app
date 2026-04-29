"""Add missing updated_at to retail_stock_movements

Revision ID: v6q1r2s3t4u5
Revises: u5p9j4k2l8m6
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa

revision = "v6q1r2s3t4u5"
down_revision = "u5p9j4k2l8m6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "retail_stock_movements",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # Also add to sale_appointments which was created without it
    op.add_column(
        "sale_appointments",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("sale_appointments", "updated_at")
    op.drop_column("retail_stock_movements", "updated_at")
