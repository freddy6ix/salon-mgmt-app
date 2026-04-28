"""Add tenant_promotions table and promotion_id to sale_items

Revision ID: n7i2d5e8f3b1
Revises: m6h1c4d7e9f2
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'n7i2d5e8f3b1'
down_revision = 'm6h1c4d7e9f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    promo_kind = postgresql.ENUM('percent', 'amount', name='promotion_kind', create_type=False)
    promo_kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'tenant_promotions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(40), nullable=False),
        sa.Column('label', sa.String(120), nullable=False),
        sa.Column('kind', promo_kind, nullable=False),
        sa.Column('value', sa.Numeric(10, 2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tenant_promotions_tenant_id', 'tenant_promotions', ['tenant_id'])

    op.add_column('sale_items',
        sa.Column('promotion_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_sale_items_promotion_id', 'sale_items', 'tenant_promotions',
        ['promotion_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_sale_items_promotion_id', 'sale_items', type_='foreignkey')
    op.drop_column('sale_items', 'promotion_id')
    op.drop_table('tenant_promotions')
    postgresql.ENUM(name='promotion_kind', create_type=False).drop(op.get_bind(), checkfirst=True)
