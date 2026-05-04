"""Add language preferences to tenant/user/client and create translation tables

Revision ID: a2b3c4d5e6f7
Revises: z1a2b3c4d5e6
Create Date: 2026-05-04

"""
import uuid
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "a2b3c4d5e6f7"
down_revision = "z1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Language preference columns ──────────────────────────────────────────
    op.add_column("tenants", sa.Column("default_language", sa.String(5), nullable=False, server_default="en"))
    op.add_column("users",   sa.Column("language_preference", sa.String(5), nullable=False, server_default="en"))
    op.add_column("clients", sa.Column("language_preference", sa.String(5), nullable=False, server_default="en"))

    # ── service_category_translations ────────────────────────────────────────
    op.create_table(
        "service_category_translations",
        sa.Column("id",          UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id",   UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), nullable=False),
        sa.Column("language",    sa.String(5),       nullable=False),
        sa.Column("name",        sa.String(255),     nullable=False),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["service_categories.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("category_id", "language", name="uq_service_cat_tr_cat_lang"),
    )
    op.create_index("ix_service_cat_tr_category_id", "service_category_translations", ["category_id"])
    op.create_index("ix_service_cat_tr_tenant_id",   "service_category_translations", ["tenant_id"])

    # ── service_translations ─────────────────────────────────────────────────
    op.create_table(
        "service_translations",
        sa.Column("id",          UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id",   UUID(as_uuid=True), nullable=False),
        sa.Column("service_id",  UUID(as_uuid=True), nullable=False),
        sa.Column("language",    sa.String(5),       nullable=False),
        sa.Column("name",        sa.String(255),     nullable=False),
        sa.Column("description", sa.Text,            nullable=True),
        sa.Column("suggestions", sa.Text,            nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("service_id", "language", name="uq_service_tr_service_lang"),
    )
    op.create_index("ix_service_tr_service_id", "service_translations", ["service_id"])
    op.create_index("ix_service_tr_tenant_id",  "service_translations", ["tenant_id"])

    # ── retail_item_translations ─────────────────────────────────────────────
    op.create_table(
        "retail_item_translations",
        sa.Column("id",             UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id",      UUID(as_uuid=True), nullable=False),
        sa.Column("retail_item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("language",       sa.String(5),       nullable=False),
        sa.Column("name",           sa.String(200),     nullable=False),
        sa.Column("description",    sa.Text,            nullable=True),
        sa.Column("created_at",     sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",     sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["retail_item_id"], ["retail_items.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("retail_item_id", "language", name="uq_retail_item_tr_item_lang"),
    )
    op.create_index("ix_retail_item_tr_retail_item_id", "retail_item_translations", ["retail_item_id"])
    op.create_index("ix_retail_item_tr_tenant_id",      "retail_item_translations", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("retail_item_translations")
    op.drop_table("service_translations")
    op.drop_table("service_category_translations")
    op.drop_column("clients", "language_preference")
    op.drop_column("users",   "language_preference")
    op.drop_column("tenants", "default_language")
