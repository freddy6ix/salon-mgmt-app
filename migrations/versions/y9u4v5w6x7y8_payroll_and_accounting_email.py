"""Add accounting_from_address to email config and TenantPayrollConfig table

Revision ID: y9u4v5w6x7y8
Revises: x8s3t4u5v6w7
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa

revision = "y9u4v5w6x7y8"
down_revision = "x8s3t4u5v6w7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Second from_address on email config (for accounting/payroll emails)
    op.add_column(
        "tenant_email_configs",
        sa.Column("accounting_from_address", sa.String(255), nullable=True),
    )

    # Payroll provider config
    op.create_table(
        "tenant_payroll_configs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("provider_name", sa.String(255), nullable=True),
        sa.Column("provider_email", sa.String(255), nullable=True),
        sa.Column("client_id", sa.String(100), nullable=True),
        sa.Column("signature", sa.String(100), nullable=True),
        sa.Column("footer", sa.Text, nullable=True),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_payroll_config"),
    )


def downgrade() -> None:
    op.drop_table("tenant_payroll_configs")
    op.drop_column("tenant_email_configs", "accounting_from_address")
