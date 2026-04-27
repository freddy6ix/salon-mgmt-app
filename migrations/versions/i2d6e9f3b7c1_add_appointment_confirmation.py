"""Add appointment confirmation columns

Revision ID: i2d6e9f3b7c1
Revises: h1c5d8e2a4f9
Create Date: 2026-04-27

Adds confirmation_status + draft + sent columns to appointments. Tracks
the staff-initiated client-confirmation email flow (P2-2): draft, send,
or skip — explicit, never automatic.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'i2d6e9f3b7c1'
down_revision = 'h1c5d8e2a4f9'
branch_labels = None
depends_on = None


CONFIRMATION_STATUSES = ('not_sent', 'draft', 'sent', 'skipped')


def upgrade() -> None:
    confirmation_status = sa.Enum(*CONFIRMATION_STATUSES, name='confirmationstatus')
    confirmation_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'appointments',
        sa.Column(
            'confirmation_status',
            confirmation_status,
            nullable=False,
            server_default='not_sent',
        ),
    )
    op.add_column('appointments', sa.Column('confirmation_draft_subject', sa.Text(), nullable=True))
    op.add_column('appointments', sa.Column('confirmation_draft_body', sa.Text(), nullable=True))
    op.add_column('appointments', sa.Column('confirmation_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        'appointments',
        sa.Column('confirmation_sent_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_appointments_confirmation_sent_by_user',
        'appointments',
        'users',
        ['confirmation_sent_by_user_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_appointments_confirmation_sent_by_user', 'appointments', type_='foreignkey')
    op.drop_column('appointments', 'confirmation_sent_by_user_id')
    op.drop_column('appointments', 'confirmation_sent_at')
    op.drop_column('appointments', 'confirmation_draft_body')
    op.drop_column('appointments', 'confirmation_draft_subject')
    op.drop_column('appointments', 'confirmation_status')
    sa.Enum(name='confirmationstatus').drop(op.get_bind(), checkfirst=True)
