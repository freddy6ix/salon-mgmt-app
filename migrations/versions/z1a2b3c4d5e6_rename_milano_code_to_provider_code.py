"""Rename milano_code to provider_code on providers and clients

Revision ID: z1a2b3c4d5e6
Revises: y9u4v5w6x7y8
Create Date: 2026-04-30

"""
from alembic import op

revision = "z1a2b3c4d5e6"
down_revision = "y9u4v5w6x7y8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("providers", "milano_code", new_column_name="provider_code")
    op.alter_column("clients", "milano_code", new_column_name="legacy_id")


def downgrade() -> None:
    op.alter_column("providers", "provider_code", new_column_name="milano_code")
    op.alter_column("clients", "legacy_id", new_column_name="milano_code")
