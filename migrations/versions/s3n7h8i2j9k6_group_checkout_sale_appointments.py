"""Replace Sale.appointment_id with sale_appointments junction (group checkout)

Revision ID: s3n7h8i2j9k6
Revises: r2m6h7i1j8k5
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "s3n7h8i2j9k6"
down_revision = "r2m6h7i1j8k5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create junction table
    op.create_table(
        "sale_appointments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("sale_id", UUID(as_uuid=True), sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("appointment_id", UUID(as_uuid=True), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sale_appointments_sale_id", "sale_appointments", ["sale_id"])
    op.create_index("ix_sale_appointments_tenant_id", "sale_appointments", ["tenant_id"])
    op.create_unique_constraint("uq_sale_appointment_appt", "sale_appointments", ["appointment_id"])

    # Migrate existing data (pre-UAT: small data volume, no prod risk)
    op.execute("""
        INSERT INTO sale_appointments (id, tenant_id, sale_id, appointment_id, created_at)
        SELECT gen_random_uuid(), tenant_id, id, appointment_id, COALESCE(completed_at, now())
        FROM sales
        WHERE appointment_id IS NOT NULL
    """)

    # Drop old column
    op.drop_constraint("uq_sale_appointment", "sales", type_="unique")
    op.drop_column("sales", "appointment_id")


def downgrade() -> None:
    op.add_column("sales", sa.Column("appointment_id", UUID(as_uuid=True), nullable=True))
    op.execute("""
        UPDATE sales s
        SET appointment_id = sa.appointment_id
        FROM sale_appointments sa
        WHERE sa.sale_id = s.id
    """)
    op.create_unique_constraint("uq_sale_appointment", "sales", ["appointment_id"])
    op.drop_index("ix_sale_appointments_tenant_id", table_name="sale_appointments")
    op.drop_index("ix_sale_appointments_sale_id", table_name="sale_appointments")
    op.drop_constraint("uq_sale_appointment_appt", "sale_appointments", type_="unique")
    op.drop_table("sale_appointments")
