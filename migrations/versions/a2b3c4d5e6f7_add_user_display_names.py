"""Add first_name, last_name to users

Revision ID: a2b3c4d5e6f7
Revises: z1a2b3c4d5e6
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

revision = 'a2b3c4d5e6f7'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
