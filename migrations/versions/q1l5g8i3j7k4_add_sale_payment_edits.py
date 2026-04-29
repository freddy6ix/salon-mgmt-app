"""Add sale_payment_edits audit table

Revision ID: q1l5g8i3j7k4
Revises: p9k4f7h2i6e3
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa

revision = 'q1l5g8i3j7k4'
down_revision = 'p9k4f7h2i6e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sale_payment_edits',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sale_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edited_by_user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('before_json', sa.Text, nullable=False),
        sa.Column('after_json', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id']),
        sa.ForeignKeyConstraint(['edited_by_user_id'], ['users.id']),
    )
    op.create_index('ix_sale_payment_edits_sale_id', 'sale_payment_edits', ['sale_id'])
    op.create_index('ix_sale_payment_edits_tenant_id', 'sale_payment_edits', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('ix_sale_payment_edits_tenant_id', 'sale_payment_edits')
    op.drop_index('ix_sale_payment_edits_sale_id', 'sale_payment_edits')
    op.drop_table('sale_payment_edits')
