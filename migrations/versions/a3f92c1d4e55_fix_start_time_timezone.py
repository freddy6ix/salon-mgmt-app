"""fix appointment_item.start_time to timezone-naive

Revision ID: a3f92c1d4e55
Revises: 1113f8542f00
Create Date: 2026-04-21

All times in the system are stored as salon-local wall-clock time with no
timezone offset.  start_time was accidentally created as TIMESTAMPTZ; this
converts it to plain TIMESTAMP so the API no longer returns a trailing 'Z'
that causes the frontend to apply a UTC→local offset.
"""
from alembic import op

revision = 'a3f92c1d4e55'
down_revision = '1113f8542f00'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE appointment_items "
        "ALTER COLUMN start_time TYPE TIMESTAMP WITHOUT TIME ZONE"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE appointment_items "
        "ALTER COLUMN start_time TYPE TIMESTAMP WITH TIME ZONE"
    )
