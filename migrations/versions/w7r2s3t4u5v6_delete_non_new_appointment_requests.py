"""One-off: delete all non-new appointment requests (reviewed, converted, declined)

Revision ID: w7r2s3t4u5v6
Revises: v6q1r2s3t4u5
Create Date: 2026-04-29

"""
from alembic import op

revision = "w7r2s3t4u5v6"
down_revision = "v6q1r2s3t4u5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Null FK references that point back to the requests being deleted
    op.execute("""
        UPDATE appointments
        SET request_id = NULL
        WHERE request_id IN (
            SELECT id FROM appointment_requests
            WHERE status IN ('reviewed', 'converted', 'declined')
        )
    """)
    # Delete child items first (FK to appointment_requests.id)
    op.execute("""
        DELETE FROM appointment_request_items
        WHERE request_id IN (
            SELECT id FROM appointment_requests
            WHERE status IN ('reviewed', 'converted', 'declined')
        )
    """)
    op.execute("""
        DELETE FROM appointment_requests
        WHERE status IN ('reviewed', 'converted', 'declined')
    """)


def downgrade() -> None:
    pass  # data deletion is not reversible
