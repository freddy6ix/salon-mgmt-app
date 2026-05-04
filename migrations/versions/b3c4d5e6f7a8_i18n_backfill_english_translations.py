"""Backfill English translation rows from existing name/description columns

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-05-04

"""
from alembic import op

revision = "b3c4d5e6f7a8"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO service_category_translations
            (id, tenant_id, category_id, language, name, created_at, updated_at)
        SELECT gen_random_uuid(), tenant_id, id, 'en', name, now(), now()
        FROM service_categories
        ON CONFLICT (category_id, language) DO NOTHING
    """)

    op.execute("""
        INSERT INTO service_translations
            (id, tenant_id, service_id, language, name, description, suggestions, created_at, updated_at)
        SELECT gen_random_uuid(), tenant_id, id, 'en', name, description, suggestions, now(), now()
        FROM services
        ON CONFLICT (service_id, language) DO NOTHING
    """)

    op.execute("""
        INSERT INTO retail_item_translations
            (id, tenant_id, retail_item_id, language, name, description, created_at, updated_at)
        SELECT gen_random_uuid(), tenant_id, id, 'en', name, description, now(), now()
        FROM retail_items
        ON CONFLICT (retail_item_id, language) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM service_category_translations WHERE language = 'en'")
    op.execute("DELETE FROM service_translations WHERE language = 'en'")
    op.execute("DELETE FROM retail_item_translations WHERE language = 'en'")
