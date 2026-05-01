"""Fix appointment item status for imported future bookings

Items imported from the legacy system as future bookings were incorrectly
set to 'cancelled'. The parent appointments are 'confirmed', so the items
should be 'confirmed' too.

Revision ID: a1b2c3d4e5f6
Revises: z1a2b3c4d5e6
Create Date: 2026-05-01

"""
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = ("o8j3e6f9g4c2", "z1a2b3c4d5e6")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE appointment_items
        SET status = 'confirmed'
        WHERE status = 'cancelled'
          AND appointment_id IN (
              SELECT id FROM appointments
              WHERE source = 'staff_entered'
                AND status = 'confirmed'
          )
    """)


def downgrade() -> None:
    pass
