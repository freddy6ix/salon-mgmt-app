"""Add cash_reconciliations and petty_cash_entries tables

Revision ID: m6h1c4d7e9f2
Revises: l5g9b3c1e8f4
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'm6h1c4d7e9f2'
down_revision = 'l5g9b3c1e8f4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    recon_status = postgresql.ENUM('open', 'closed', name='reconciliation_status', create_type=False)
    recon_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'cash_reconciliations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_date', sa.Date(), nullable=False),
        sa.Column('opening_balance', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('counted_balance', sa.Numeric(10, 2), nullable=True),
        sa.Column('deposit_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('closing_balance', sa.Numeric(10, 2), nullable=True),
        sa.Column('variance', sa.Numeric(10, 2), nullable=True),
        sa.Column('variance_note', sa.Text(), nullable=True),
        sa.Column('status', recon_status, nullable=False, server_default='open'),
        sa.Column('closed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['closed_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'business_date', name='uq_cash_reconciliation_date'),
    )
    op.create_index('ix_cash_reconciliations_tenant_id', 'cash_reconciliations', ['tenant_id'])
    op.create_index('ix_cash_reconciliations_business_date', 'cash_reconciliations', ['business_date'])

    op.create_table(
        'petty_cash_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reconciliation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['reconciliation_id'], ['cash_reconciliations.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_petty_cash_entries_tenant_id', 'petty_cash_entries', ['tenant_id'])
    op.create_index('ix_petty_cash_entries_reconciliation_id', 'petty_cash_entries', ['reconciliation_id'])


def downgrade() -> None:
    op.drop_table('petty_cash_entries')
    op.drop_table('cash_reconciliations')
    postgresql.ENUM(name='reconciliation_status', create_type=False).drop(op.get_bind(), checkfirst=True)
