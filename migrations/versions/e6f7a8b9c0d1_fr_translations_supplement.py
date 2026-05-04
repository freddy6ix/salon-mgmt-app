"""Supplement French translations: known extras + English fallback for any remainder

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-05-04
"""
from alembic import op

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None

# Additional category translations not covered by the initial migration
_EXTRA_CATEGORY_FR = {
    "Miscellaneous": "Divers",
    "Treatments":    "Traitements",
    "Retail":        "Produits",
    "Other":         "Autre",
}

# Additional service translations not covered by the initial migration
_EXTRA_SERVICE_FR = {
    "Consultation":                   "Consultation",
    "Styling Consultation":           "Consultation coiffure",
    "Milbon Treatment (stand-alone)": "Traitement Milbon (autonome)",
    "Colour Consultation":            "Consultation couleur",
    "Keratin Treatment":              "Traitement kératine",
    "Deep Conditioning":              "Soin en profondeur",
    "Scalp Treatment":                "Soin du cuir chevelu",
    "Bang Trim":                      "Retouche frange",
    "Neck Trim":                      "Retouche nuque",
}


def upgrade() -> None:
    # ── Known extra category translations ────────────────────────────────────
    for en_name, fr_name in _EXTRA_CATEGORY_FR.items():
        en_safe = en_name.replace("'", "''")
        fr_safe = fr_name.replace("'", "''")
        op.execute(f"""
            INSERT INTO service_category_translations
                (id, tenant_id, category_id, language, name, created_at, updated_at)
            SELECT gen_random_uuid(), sc.tenant_id, sc.id, 'fr', '{fr_safe}', now(), now()
            FROM service_categories sc
            WHERE sc.name = '{en_safe}'
            ON CONFLICT (category_id, language) DO UPDATE
                SET name = EXCLUDED.name, updated_at = now()
        """)

    # ── Known extra service translations ─────────────────────────────────────
    for en_name, fr_name in _EXTRA_SERVICE_FR.items():
        en_safe = en_name.replace("'", "''")
        fr_safe = fr_name.replace("'", "''")
        op.execute(f"""
            INSERT INTO service_translations
                (id, tenant_id, service_id, language, name, description, suggestions, created_at, updated_at)
            SELECT gen_random_uuid(), s.tenant_id, s.id, 'fr', '{fr_safe}', NULL, NULL, now(), now()
            FROM services s
            WHERE s.name = '{en_safe}'
            ON CONFLICT (service_id, language) DO UPDATE
                SET name = EXCLUDED.name, updated_at = now()
        """)

    # ── Fallback: copy English name for anything still untranslated ───────────
    # Safe to run repeatedly — only fills genuine gaps.
    op.execute("""
        INSERT INTO service_category_translations
            (id, tenant_id, category_id, language, name, created_at, updated_at)
        SELECT gen_random_uuid(), en.tenant_id, en.category_id, 'fr', en.name, now(), now()
        FROM service_category_translations en
        WHERE en.language = 'en'
          AND NOT EXISTS (
            SELECT 1 FROM service_category_translations fr2
            WHERE fr2.category_id = en.category_id AND fr2.language = 'fr'
          )
        ON CONFLICT (category_id, language) DO NOTHING
    """)

    op.execute("""
        INSERT INTO service_translations
            (id, tenant_id, service_id, language, name, description, suggestions, created_at, updated_at)
        SELECT gen_random_uuid(), en.tenant_id, en.service_id, 'fr',
               en.name, en.description, en.suggestions, now(), now()
        FROM service_translations en
        WHERE en.language = 'en'
          AND NOT EXISTS (
            SELECT 1 FROM service_translations fr2
            WHERE fr2.service_id = en.service_id AND fr2.language = 'fr'
          )
        ON CONFLICT (service_id, language) DO NOTHING
    """)

    op.execute("""
        INSERT INTO retail_item_translations
            (id, tenant_id, retail_item_id, language, name, description, created_at, updated_at)
        SELECT gen_random_uuid(), en.tenant_id, en.retail_item_id, 'fr',
               en.name, en.description, now(), now()
        FROM retail_item_translations en
        WHERE en.language = 'en'
          AND NOT EXISTS (
            SELECT 1 FROM retail_item_translations fr2
            WHERE fr2.retail_item_id = en.retail_item_id AND fr2.language = 'fr'
          )
        ON CONFLICT (retail_item_id, language) DO NOTHING
    """)


def downgrade() -> None:
    # Only remove rows we explicitly added — leave the initial migration's rows alone
    op.execute("""
        DELETE FROM service_category_translations
        WHERE language = 'fr'
          AND category_id IN (
            SELECT id FROM service_categories
            WHERE name IN ('Miscellaneous','Treatments','Retail','Other')
          )
    """)
    op.execute("""
        DELETE FROM service_translations
        WHERE language = 'fr'
          AND service_id IN (
            SELECT id FROM services
            WHERE name IN (
              'Consultation','Styling Consultation','Milbon Treatment (stand-alone)',
              'Colour Consultation','Keratin Treatment','Deep Conditioning',
              'Scalp Treatment','Bang Trim','Neck Trim'
            )
          )
    """)
