"""Add slot_minutes to tenant

Revision ID: f3b1e8d2c7a5
Revises: e2c4a9f1b7d3
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'f3b1e8d2c7a5'
down_revision = 'e2c4a9f1b7d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('slot_minutes', sa.Integer(), nullable=False, server_default='10'))


def downgrade() -> None:
    op.drop_column('tenants', 'slot_minutes')
