"""Add reminder_send_time to tenants

Revision ID: c5d6e7f8a9b0
Revises: e6f7a8b9c0d1
Create Date: 2026-05-04

"""
import sqlalchemy as sa
from alembic import op

revision = "c5d6e7f8a9b0"
down_revision = "e6f7a8b9c0d1"
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
