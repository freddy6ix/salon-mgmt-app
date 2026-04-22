"""add tenant branding fields

Revision ID: f2a9e1d8c5b3
Revises: c4d82e1f5a09
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'f2a9e1d8c5b3'
down_revision = 'c4d82e1f5a09'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('logo_url', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('brand_color', sa.String(7), nullable=True))


def downgrade() -> None:
    op.drop_column('tenants', 'brand_color')
    op.drop_column('tenants', 'logo_url')
