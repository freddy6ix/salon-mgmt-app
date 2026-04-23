"""add tenant_email_configs table

Revision ID: e2c4a9f1b7d3
Revises: d1b3f8e2a4c6
Create Date: 2026-04-23

Per-tenant SMTP configuration. Replaces the hard-coded Resend
environment variables with admin-configurable SMTP settings stored in
the database. Works with any SMTP provider (Gmail Workspace, Resend
SMTP, SendGrid, etc.).
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = 'e2c4a9f1b7d3'
down_revision = 'd1b3f8e2a4c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tenant_email_configs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('smtp_host', sa.String(255), nullable=False),
        sa.Column('smtp_port', sa.Integer, nullable=False, server_default='587'),
        sa.Column('smtp_username', sa.String(255), nullable=False),
        sa.Column('smtp_password', sa.String(1024), nullable=False),
        sa.Column('smtp_use_tls', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('from_address', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('tenant_id', name='uq_tenant_email_config'),
    )


def downgrade() -> None:
    op.drop_table('tenant_email_configs')
