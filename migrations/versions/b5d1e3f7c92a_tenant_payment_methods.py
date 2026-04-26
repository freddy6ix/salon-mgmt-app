"""Replace payment_type enum with tenant_payment_methods table

Revision ID: b5d1e3f7c92a
Revises: a4c8d2e9f1b7
Create Date: 2026-04-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b5d1e3f7c92a'
down_revision = 'a4c8d2e9f1b7'
branch_labels = None
depends_on = None


# Default seed: maps the legacy `payment_type` enum values to (label, kind).
DEFAULT_METHODS: list[tuple[str, str, str, int]] = [
    # (code, label, kind, sort_order)
    ('cash',       'Cash',       'cash',     10),
    ('debit',      'Debit',      'card',     20),
    ('visa',       'Visa',       'card',     30),
    ('mastercard', 'Mastercard', 'card',     40),
    ('amex',       'AMEX',       'card',     50),
    ('e_transfer', 'E-Transfer', 'transfer', 60),
]


def upgrade() -> None:
    bind = op.get_bind()

    # 1. payment_method_kind enum
    kind_enum = postgresql.ENUM('cash', 'card', 'transfer', 'other',
                                name='payment_method_kind', create_type=False)
    kind_enum.create(bind, checkfirst=True)

    # 2. tenant_payment_methods table
    op.create_table(
        'tenant_payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(40), nullable=False),
        sa.Column('label', sa.String(80), nullable=False),
        sa.Column('kind', kind_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_tenant_payment_method_code'),
    )
    op.create_index('ix_tenant_payment_methods_tenant_id', 'tenant_payment_methods', ['tenant_id'])

    # 3. Seed defaults for every existing tenant.
    for code, label, kind, sort_order in DEFAULT_METHODS:
        bind.execute(
            sa.text("""
                INSERT INTO tenant_payment_methods (id, tenant_id, code, label, kind, is_active, sort_order)
                SELECT gen_random_uuid(), t.id, :code, :label, CAST(:kind AS payment_method_kind), TRUE, :sort_order
                FROM tenants t
            """),
            {'code': code, 'label': label, 'kind': kind, 'sort_order': sort_order},
        )

    # 4. Add nullable payment_method_id column to sale_payments.
    op.add_column(
        'sale_payments',
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_sale_payments_payment_method_id', 'sale_payments', ['payment_method_id'])

    # 5. Backfill payment_method_id from the legacy payment_type enum.
    bind.execute(sa.text("""
        UPDATE sale_payments sp
        SET payment_method_id = tpm.id
        FROM tenant_payment_methods tpm
        WHERE tpm.tenant_id = sp.tenant_id
          AND tpm.code = sp.payment_type::text
    """))

    # 6. Now require payment_method_id and add the FK.
    op.alter_column('sale_payments', 'payment_method_id', nullable=False)
    op.create_foreign_key(
        'fk_sale_payments_payment_method_id',
        'sale_payments', 'tenant_payment_methods',
        ['payment_method_id'], ['id'],
    )

    # 7. Drop legacy column and enum type.
    op.drop_column('sale_payments', 'payment_type')
    postgresql.ENUM(name='payment_type', create_type=False).drop(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()

    # Recreate legacy enum.
    payment_type_enum = postgresql.ENUM(
        'amex', 'cash', 'debit', 'e_transfer', 'mastercard', 'visa',
        name='payment_type', create_type=False,
    )
    payment_type_enum.create(bind, checkfirst=True)

    # Add legacy column nullable, backfill from method code, then enforce NOT NULL.
    op.add_column(
        'sale_payments',
        sa.Column('payment_type', payment_type_enum, nullable=True),
    )
    bind.execute(sa.text("""
        UPDATE sale_payments sp
        SET payment_type = CAST(tpm.code AS payment_type)
        FROM tenant_payment_methods tpm
        WHERE tpm.id = sp.payment_method_id
          AND tpm.code IN ('amex', 'cash', 'debit', 'e_transfer', 'mastercard', 'visa')
    """))
    op.alter_column('sale_payments', 'payment_type', nullable=False)

    # Drop the FK, the new column, and the lookup table.
    op.drop_constraint('fk_sale_payments_payment_method_id', 'sale_payments', type_='foreignkey')
    op.drop_index('ix_sale_payments_payment_method_id', table_name='sale_payments')
    op.drop_column('sale_payments', 'payment_method_id')

    op.drop_index('ix_tenant_payment_methods_tenant_id', table_name='tenant_payment_methods')
    op.drop_table('tenant_payment_methods')
    postgresql.ENUM(name='payment_method_kind', create_type=False).drop(bind, checkfirst=True)
