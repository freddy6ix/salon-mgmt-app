"""Add reminder_enabled and reminder_lead_hours to tenants

Revision ID: r2m6h7i1j8k5
Revises: q1l5g8i3j7k4
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa

revision = "r2m6h7i1j8k5"
down_revision = "q1l5g8i3j7k4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("reminder_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("tenants", sa.Column("reminder_lead_hours", sa.Integer(), nullable=False, server_default="24"))


def downgrade() -> None:
    op.drop_column("tenants", "reminder_lead_hours")
    op.drop_column("tenants", "reminder_enabled")
