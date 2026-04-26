"""Add duration_minutes override to provider_service_prices

Revision ID: f4a8c2d917b6
Revises: e9b1d4f7c382
Create Date: 2026-04-26

NULL means use the service's default duration; a value overrides it for
this provider only. Mirrors how price already works (a row exists when
the provider offers the service; columns may override service defaults).
"""
from alembic import op
import sqlalchemy as sa


revision = 'f4a8c2d917b6'
down_revision = 'e9b1d4f7c382'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'provider_service_prices',
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('provider_service_prices', 'duration_minutes')
