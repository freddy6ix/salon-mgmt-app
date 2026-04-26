"""Drop unused Service fields: haircut_type, is_addon, is_gst_exempt, is_pst_exempt

Revision ID: e9b1d4f7c382
Revises: d8f3a1c92e76
Create Date: 2026-04-26

- haircut_type: not a useful classification on a Service.
- is_addon: would only matter with explicit linkage rules to a primary
  service; that's out of scope.
- is_gst_exempt / is_pst_exempt: never honored at checkout — sale tax
  computation uses flat tenant rates on the subtotal, not per-line flags.
  Can be reintroduced cleanly when per-line tax behavior is implemented.

Pre-UAT lifecycle: no production data to preserve; clean drop.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'e9b1d4f7c382'
down_revision = 'd8f3a1c92e76'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.drop_column('services', 'haircut_type')
    op.drop_column('services', 'is_addon')
    op.drop_column('services', 'is_gst_exempt')
    op.drop_column('services', 'is_pst_exempt')
    postgresql.ENUM(name='haircuttype', create_type=False).drop(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    haircut_enum = postgresql.ENUM('type_1', 'type_2', 'type_2_plus',
                                   name='haircuttype', create_type=False)
    haircut_enum.create(bind, checkfirst=True)
    op.add_column('services', sa.Column('haircut_type', haircut_enum, nullable=True))
    op.add_column('services', sa.Column('is_addon', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('services', sa.Column('is_gst_exempt', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('services', sa.Column('is_pst_exempt', sa.Boolean(), nullable=False, server_default=sa.false()))
