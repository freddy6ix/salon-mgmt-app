"""Add time_format column to tenants

Revision ID: l5g9b3c1e8f4
Revises: k4f8a2b9d6e7
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa

revision = 'l5g9b3c1e8f4'
down_revision = 'k4f8a2b9d6e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('time_format', sa.String(3), nullable=False, server_default='12h'))


def downgrade() -> None:
    op.drop_column('tenants', 'time_format')
