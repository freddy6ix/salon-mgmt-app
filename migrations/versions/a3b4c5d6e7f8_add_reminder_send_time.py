"""Add reminder_send_time to tenants

Revision ID: a3b4c5d6e7f8
Revises: z1a2b3c4d5e6
Create Date: 2026-05-04

"""
import sqlalchemy as sa
from alembic import op

revision = "a3b4c5d6e7f8"
down_revision = "z1a2b3c4d5e6"
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
