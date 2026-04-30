"""Add staff management fields to providers

Revision ID: x8s3t4u5v6w7
Revises: w7r2s3t4u5v6
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "x8s3t4u5v6w7"
down_revision = "w7r2s3t4u5v6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add commission to pay_type enum
    op.execute("ALTER TYPE paytype ADD VALUE IF NOT EXISTS 'commission'")

    # Add EI rate type enum
    op.execute("CREATE TYPE eiratetype AS ENUM ('normal', 'reduced')")

    op.add_column("providers", sa.Column("sex", sa.String(20), nullable=True))
    op.add_column("providers", sa.Column("job_title", sa.String(100), nullable=True))
    op.add_column("providers", sa.Column("hire_date", sa.Date(), nullable=True))
    op.add_column("providers", sa.Column("first_day_worked", sa.Date(), nullable=True))
    op.add_column("providers", sa.Column("certification", sa.String(255), nullable=True))
    op.add_column("providers", sa.Column("vacation_pct", sa.Numeric(5, 2), nullable=True, server_default="4.00"))

    # Banking (account number encrypted like SIN)
    op.add_column("providers", sa.Column("bank_institution_no", sa.String(10), nullable=True))
    op.add_column("providers", sa.Column("bank_transit_no", sa.String(10), nullable=True))
    op.add_column("providers", sa.Column("bank_account_encrypted", sa.String(500), nullable=True))

    # Tax
    op.add_column("providers", sa.Column("cpp_exempt", sa.Boolean(), nullable=True))
    op.add_column("providers", sa.Column("ei_exempt", sa.Boolean(), nullable=True))
    op.add_column("providers", sa.Column(
        "ei_rate_type",
        sa.Enum("normal", "reduced", name="eiratetype", create_type=False),
        nullable=True,
    ))
    op.add_column("providers", sa.Column("province_of_taxation", sa.String(50), nullable=True))
    op.add_column("providers", sa.Column("wcb_csst_exempt", sa.Boolean(), nullable=True))
    op.add_column("providers", sa.Column("td1_federal_credit", sa.Numeric(10, 2), nullable=True))
    op.add_column("providers", sa.Column("td1_provincial_credit", sa.Numeric(10, 2), nullable=True))

    # Commission compensation fields
    op.add_column("providers", sa.Column("hourly_minimum", sa.Numeric(10, 2), nullable=True))
    op.add_column("providers", sa.Column("retail_commission_pct", sa.Numeric(5, 2), nullable=True, server_default="10.00"))
    op.add_column("providers", sa.Column("commission_tiers", postgresql.JSONB(), nullable=True))
    op.add_column("providers", sa.Column("product_fee_styling_flat", sa.Numeric(10, 2), nullable=True))
    op.add_column("providers", sa.Column("product_fee_colour_pct", sa.Numeric(5, 2), nullable=True))


def downgrade() -> None:
    for col in [
        "sex", "job_title", "hire_date", "first_day_worked", "certification", "vacation_pct",
        "bank_institution_no", "bank_transit_no", "bank_account_encrypted",
        "cpp_exempt", "ei_exempt", "ei_rate_type", "province_of_taxation", "wcb_csst_exempt",
        "td1_federal_credit", "td1_provincial_credit",
        "hourly_minimum", "retail_commission_pct", "commission_tiers",
        "product_fee_styling_flat", "product_fee_colour_pct",
    ]:
        op.drop_column("providers", col)
    op.execute("DROP TYPE IF EXISTS eiratetype")
