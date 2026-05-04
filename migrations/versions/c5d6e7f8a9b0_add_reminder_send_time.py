"""Add reminder_send_time to tenants

Revision ID: c5d6e7f8a9b0
Revises: a3b4c5d6e7f8
Create Date: 2026-05-04

"""
import sqlalchemy as sa
from alembic import op

revision = "c5d6e7f8a9b0"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "reminder_send_time",
            sa.String(5),
            nullable=False,
            server_default="09:00",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "reminder_send_time")
