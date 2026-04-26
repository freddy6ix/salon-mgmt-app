"""Add time_blocks table

Revision ID: h1c5d8e2a4f9
Revises: g7e3b9d2c4a8
Create Date: 2026-04-26

Time blocks are non-bookable spans on a provider's column (lunch,
meeting, training, sick). Behave like appointments on the grid but
have no client/service — just a note.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'h1c5d8e2a4f9'
down_revision = 'g7e3b9d2c4a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'time_blocks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=False), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_time_blocks_tenant_id', 'time_blocks', ['tenant_id'])
    op.create_index('ix_time_blocks_provider_id', 'time_blocks', ['provider_id'])
    op.create_index('ix_time_blocks_start_time', 'time_blocks', ['start_time'])


def downgrade() -> None:
    op.drop_index('ix_time_blocks_start_time', table_name='time_blocks')
    op.drop_index('ix_time_blocks_provider_id', table_name='time_blocks')
    op.drop_index('ix_time_blocks_tenant_id', table_name='time_blocks')
    op.drop_table('time_blocks')
