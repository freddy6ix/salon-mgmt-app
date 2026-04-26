"""Add sales, sale_items, sale_payments tables

Revision ID: a4c8d2e9f1b7
Revises: f3b1e8d2c7a5
Create Date: 2026-04-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a4c8d2e9f1b7'
down_revision = 'f3b1e8d2c7a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    sale_status = sa.Enum('pending', 'completed', name='sale_status')
    payment_type = sa.Enum('amex', 'cash', 'debit', 'e_transfer', 'mastercard', 'visa', name='payment_type')
    sale_status.create(op.get_bind(), checkfirst=True)
    payment_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'sales',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('discount_total', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('gst_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('pst_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('tip_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('total', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('status', sale_status, nullable=False, server_default='pending'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['completed_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id', name='uq_sale_appointment'),
    )
    op.create_index('ix_sales_tenant_id', 'sales', ['tenant_id'])
    op.create_index('ix_sales_appointment_id', 'sales', ['appointment_id'])
    op.create_index('ix_sales_client_id', 'sales', ['client_id'])

    op.create_table(
        'sale_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appointment_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id']),
        sa.ForeignKeyConstraint(['appointment_item_id'], ['appointment_items.id']),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sale_items_tenant_id', 'sale_items', ['tenant_id'])
    op.create_index('ix_sale_items_sale_id', 'sale_items', ['sale_id'])

    op.create_table(
        'sale_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_type', payment_type, nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sale_payments_tenant_id', 'sale_payments', ['tenant_id'])
    op.create_index('ix_sale_payments_sale_id', 'sale_payments', ['sale_id'])


def downgrade() -> None:
    op.drop_table('sale_payments')
    op.drop_table('sale_items')
    op.drop_table('sales')
    sa.Enum(name='payment_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sale_status').drop(op.get_bind(), checkfirst=True)
