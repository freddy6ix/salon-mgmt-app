"""add guest role, client user_id, and request submitted_by_user_id

Revision ID: b2e5f9c1d3a8
Revises: a3f92c1d4e55
Create Date: 2026-04-21

Adds support for guest (customer) accounts:
- guest value in the userrole enum
- clients.user_id links a client record to its self-registered user
- appointment_requests.submitted_by_user_id tracks which guest submitted a request
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = 'b2e5f9c1d3a8'
down_revision = 'a3f92c1d4e55'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'guest'")

    op.add_column('clients', sa.Column('user_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_clients_user_id', 'clients', 'users', ['user_id'], ['id']
    )
    op.create_index('ix_clients_user_id', 'clients', ['user_id'])

    op.add_column(
        'appointment_requests',
        sa.Column('submitted_by_user_id', UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_appt_requests_submitted_by_user_id',
        'appointment_requests', 'users',
        ['submitted_by_user_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_appt_requests_submitted_by_user_id', 'appointment_requests', type_='foreignkey')
    op.drop_column('appointment_requests', 'submitted_by_user_id')

    op.drop_index('ix_clients_user_id', table_name='clients')
    op.drop_constraint('fk_clients_user_id', 'clients', type_='foreignkey')
    op.drop_column('clients', 'user_id')

    # PostgreSQL does not support removing enum values; manual rollback required if needed
