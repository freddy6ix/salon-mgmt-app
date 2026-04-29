"""Add Resend API email mode to tenant_email_configs

Revision ID: p9k4f7h2i6e3
Revises: o8j3e6f9g4c2
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa

revision = 'p9k4f7h2i6e3'
down_revision = 'ddb1dd9769c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenant_email_configs',
        sa.Column('send_mode', sa.String(20), nullable=False, server_default='smtp'))
    op.add_column('tenant_email_configs',
        sa.Column('resend_api_key', sa.String(1024), nullable=True))
    # Make SMTP-specific columns nullable (not needed in resend_api mode)
    op.alter_column('tenant_email_configs', 'smtp_host', nullable=True)
    op.alter_column('tenant_email_configs', 'smtp_username', nullable=True)
    op.alter_column('tenant_email_configs', 'smtp_password', nullable=True)


def downgrade() -> None:
    # Re-fill nulls before restoring NOT NULL constraint
    op.execute("UPDATE tenant_email_configs SET smtp_host = '' WHERE smtp_host IS NULL")
    op.execute("UPDATE tenant_email_configs SET smtp_username = '' WHERE smtp_username IS NULL")
    op.execute("UPDATE tenant_email_configs SET smtp_password = '' WHERE smtp_password IS NULL")
    op.alter_column('tenant_email_configs', 'smtp_password', nullable=False)
    op.alter_column('tenant_email_configs', 'smtp_username', nullable=False)
    op.alter_column('tenant_email_configs', 'smtp_host', nullable=False)
    op.drop_column('tenant_email_configs', 'resend_api_key')
    op.drop_column('tenant_email_configs', 'send_mode')
