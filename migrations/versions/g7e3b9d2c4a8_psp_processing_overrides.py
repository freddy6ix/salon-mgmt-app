"""Add processing_offset_minutes and processing_duration_minutes overrides to provider_service_prices

Revision ID: g7e3b9d2c4a8
Revises: f4a8c2d917b6
Create Date: 2026-04-26

NULL means use the service's default for that processing field; a value
overrides it for this provider only. Same shape as the duration_minutes
override added in f4a8c2d917b6.
"""
from alembic import op
import sqlalchemy as sa


revision = 'g7e3b9d2c4a8'
down_revision = 'f4a8c2d917b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'provider_service_prices',
        sa.Column('processing_offset_minutes', sa.Integer(), nullable=True),
    )
    op.add_column(
        'provider_service_prices',
        sa.Column('processing_duration_minutes', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('provider_service_prices', 'processing_duration_minutes')
    op.drop_column('provider_service_prices', 'processing_offset_minutes')
