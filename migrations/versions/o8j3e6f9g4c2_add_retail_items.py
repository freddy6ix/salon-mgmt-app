"""Add retail_items table and retail columns to sale_items

Revision ID: o8j3e6f9g4c2
Revises: n7i2d5e8f3b1
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'o8j3e6f9g4c2'
down_revision = 'n7i2d5e8f3b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'retail_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku', sa.String(80), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('default_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_gst_exempt', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_pst_exempt', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_retail_items_tenant_id', 'retail_items', ['tenant_id'])

    sale_item_kind = postgresql.ENUM('service', 'retail', name='sale_item_kind', create_type=False)
    sale_item_kind.create(op.get_bind(), checkfirst=True)

    op.add_column('sale_items', sa.Column('kind', sale_item_kind, nullable=False, server_default='service'))
    op.add_column('sale_items', sa.Column('retail_item_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('sale_items', sa.Column('retail_item_name', sa.String(200), nullable=True))
    op.create_foreign_key(
        'fk_sale_items_retail_item_id', 'sale_items', 'retail_items',
        ['retail_item_id'], ['id'],
    )
    # Make provider_id nullable so retail items (which have no provider) can be stored
    op.alter_column('sale_items', 'provider_id', nullable=True)


def downgrade() -> None:
    op.drop_constraint('fk_sale_items_retail_item_id', 'sale_items', type_='foreignkey')
    op.drop_column('sale_items', 'retail_item_name')
    op.drop_column('sale_items', 'retail_item_id')
    op.drop_column('sale_items', 'kind')
    postgresql.ENUM(name='sale_item_kind', create_type=False).drop(op.get_bind(), checkfirst=True)
    op.drop_table('retail_items')
