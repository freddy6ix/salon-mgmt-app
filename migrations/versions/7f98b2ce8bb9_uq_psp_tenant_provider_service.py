"""uq_psp_tenant_provider_service

Revision ID: 7f98b2ce8bb9
Revises: o8j3e6f9g4c2
Create Date: 2026-04-28 21:42:21.231605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7f98b2ce8bb9'
down_revision: Union[str, None] = 'o8j3e6f9g4c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove duplicate rows, keeping the one with the latest updated_at per
    # (tenant_id, provider_id, service_id) group before adding the constraint.
    op.execute("""
        DELETE FROM provider_service_prices
        WHERE id NOT IN (
            SELECT DISTINCT ON (tenant_id, provider_id, service_id) id
            FROM provider_service_prices
            ORDER BY tenant_id, provider_id, service_id, updated_at DESC
        )
    """)
    op.create_unique_constraint(
        'uq_psp_tenant_provider_service',
        'provider_service_prices',
        ['tenant_id', 'provider_id', 'service_id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_psp_tenant_provider_service',
        'provider_service_prices',
        type_='unique',
    )
