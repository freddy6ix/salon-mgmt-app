"""Add tenant fields for new-booking-request notifications

Revision ID: j3e7f1a8c4b2
Revises: i2d6e9f3b7c1
Create Date: 2026-04-27

When a guest submits a booking request, salon staff get notified by email
(P2-4). Two new columns on tenants control this:

- request_notifications_enabled (bool, default true)
- request_notification_recipients (text, nullable, comma-separated emails)
"""
from alembic import op
import sqlalchemy as sa


revision = 'j3e7f1a8c4b2'
down_revision = 'i2d6e9f3b7c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'tenants',
        sa.Column(
            'request_notifications_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        'tenants',
        sa.Column('request_notification_recipients', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('tenants', 'request_notification_recipients')
    op.drop_column('tenants', 'request_notifications_enabled')
