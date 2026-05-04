"""Add staff_time_entries table for check-in/check-out tracking

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-05-04

"""
import uuid
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_time_entries",
        sa.Column("id",                  UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id",           UUID(as_uuid=True), nullable=False),
        sa.Column("provider_id",         UUID(as_uuid=True), nullable=False),
        sa.Column("date",                sa.Date,            nullable=False),
        sa.Column("check_in_at",         sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out_at",        sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes",               sa.Text,            nullable=True),
        sa.Column("created_by_user_id",  UUID(as_uuid=True), nullable=True),
        sa.Column("created_at",          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"],        ["providers.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_staff_time_entries_tenant_id",   "staff_time_entries", ["tenant_id"])
    op.create_index("ix_staff_time_entries_provider_id", "staff_time_entries", ["provider_id"])
    op.create_index("ix_staff_time_entries_date",        "staff_time_entries", ["date"])


def downgrade() -> None:
    op.drop_table("staff_time_entries")
