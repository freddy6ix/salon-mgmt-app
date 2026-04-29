"""Add retail_stock_movements table (P2-13 inventory)

Revision ID: t4o8i3j1k7l5
Revises: s3n7h8i2j9k6
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "t4o8i3j1k7l5"
down_revision = "s3n7h8i2j9k6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "retail_stock_movements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("retail_item_id", UUID(as_uuid=True), sa.ForeignKey("retail_items.id"), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("receive", "sell", "adjust", "return", name="stock_movement_kind"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("sale_item_id", UUID(as_uuid=True), sa.ForeignKey("sale_items.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_retail_stock_movements_tenant_id", "retail_stock_movements", ["tenant_id"])
    op.create_index("ix_retail_stock_movements_retail_item_id", "retail_stock_movements", ["retail_item_id"])


def downgrade() -> None:
    op.drop_index("ix_retail_stock_movements_retail_item_id", table_name="retail_stock_movements")
    op.drop_index("ix_retail_stock_movements_tenant_id", table_name="retail_stock_movements")
    op.drop_table("retail_stock_movements")
    op.execute("DROP TYPE IF EXISTS stock_movement_kind")
