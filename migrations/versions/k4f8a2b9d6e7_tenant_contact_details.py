"""Add tenant contact details (address, phone, hours_summary)

Revision ID: k4f8a2b9d6e7
Revises: j3e7f1a8c4b2
Create Date: 2026-04-27

P2-18 — gives tenants real contact info that the email footer can render
and the landing page can pull from (replaces the hardcoded "1452 Yonge
Street"). Stored as discrete fields, not a free-text blob, so we can
format per locale and link to maps in future.
"""
from alembic import op
import sqlalchemy as sa


revision = 'k4f8a2b9d6e7'
down_revision = 'j3e7f1a8c4b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('address_line1', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('address_line2', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('tenants', sa.Column('region', sa.String(length=100), nullable=True))
    op.add_column('tenants', sa.Column('postal_code', sa.String(length=20), nullable=True))
    op.add_column('tenants', sa.Column('country', sa.String(length=2), nullable=True))
    op.add_column('tenants', sa.Column('phone', sa.String(length=30), nullable=True))
    op.add_column('tenants', sa.Column('hours_summary', sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column('tenants', 'hours_summary')
    op.drop_column('tenants', 'phone')
    op.drop_column('tenants', 'country')
    op.drop_column('tenants', 'postal_code')
    op.drop_column('tenants', 'region')
    op.drop_column('tenants', 'city')
    op.drop_column('tenants', 'address_line2')
    op.drop_column('tenants', 'address_line1')
