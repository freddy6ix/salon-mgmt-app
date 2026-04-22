"""add client colour notes

Revision ID: c4d82e1f5a09
Revises: a3f92c1d4e55
Create Date: 2026-04-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'c4d82e1f5a09'
down_revision = 'b2e5f9c1d3a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'client_colour_notes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id'), nullable=False, index=True),
        sa.Column('created_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('note_date', sa.Date(), nullable=False),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('client_colour_notes')
