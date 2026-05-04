"""Add French translations for services and service categories

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-05-04
"""
from alembic import op

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Category translations
# ---------------------------------------------------------------------------
_CATEGORY_FR = {
    "Colouring":  "Coloration",
    "Extensions": "Extensions",
    "Styling":    "Coiffure",
}

# ---------------------------------------------------------------------------
# Service translations
# ---------------------------------------------------------------------------
_SERVICE_FR = {
    "Accent Highlights":                    "Mèches accentuées",
    "Balayage Touch-Up":                    "Retouche balayage",
    "Blowdry":                              "Brushing",
    "Camo Colour":                          "Couleur camouflage",
    "Color Full Color":                     "Couleur complète",
    "Colour Correction":                    "Correction de couleur",
    "Extensions - Fusion":                  "Extensions - Fusion",
    "Extensions - Microbead":               "Extensions - Microbead",
    "Extensions - Tape-In":                 "Extensions - Tape-In",
    "Extensions - Weft":                    "Extensions - Weft",
    "Fringe/Bang Cut":                      "Coupe de frange",
    "Full Balayage":                        "Balayage complet",
    "Full Highlights":                      "Mèches complètes",
    "Hair Botox":                           "Botox capillaire",
    "Hair Botox Express":                   "Botox capillaire Express",
    "Hair Botox (without home care)":       "Botox capillaire (sans soins à domicile)",
    "Heat Tool Finish":                     "Finition au fer chaud",
    "Metal Detox/Olaplex (add-on)":         "Détox métal / Olaplex (supplément)",
    "Milbon Treatment":                     "Soin Milbon",
    "Milbon Treatment (add-on)":            "Soin Milbon (supplément)",
    "Partial Highlights":                   "Mèches partielles",
    "Refreshing Ends":                      "Rafraîchissement des pointes",
    "Root Touch-Up":                        "Retouche racines",
    "Root Touch-Up (bleach/high lift)":     "Retouche racines (décoloration / éclaircissement)",
    "Special Updo":                         "Coiffure de soirée",
    "Toner/Gloss":                          "Tonifiant / Brillance",
    "Toner/Gloss (add-on)":                 "Tonifiant / Brillance (supplément)",
    "Type 1 Haircut":                       "Coupe type 1",
    "Type 2 Haircut":                       "Coupe type 2",
    "Type 2+ Haircut":                      "Coupe type 2+",
    "Consultation":                         "Consultation",
    "Vivid Color":                          "Couleur vive",
}


def upgrade() -> None:
    # ── Category translations ────────────────────────────────────────────────
    for en_name, fr_name in _CATEGORY_FR.items():
        op.execute(f"""
            INSERT INTO service_category_translations
                (id, tenant_id, category_id, language, name, created_at, updated_at)
            SELECT
                gen_random_uuid(),
                sc.tenant_id,
                sc.id,
                'fr',
                '{fr_name}',
                now(),
                now()
            FROM service_categories sc
            WHERE sc.name = '{en_name}'
            ON CONFLICT (category_id, language) DO UPDATE
                SET name = EXCLUDED.name, updated_at = now()
        """)

    # ── Service translations ─────────────────────────────────────────────────
    for en_name, fr_name in _SERVICE_FR.items():
        # Escape single quotes in names
        en_safe = en_name.replace("'", "''")
        fr_safe = fr_name.replace("'", "''")
        op.execute(f"""
            INSERT INTO service_translations
                (id, tenant_id, service_id, language, name, description, suggestions, created_at, updated_at)
            SELECT
                gen_random_uuid(),
                s.tenant_id,
                s.id,
                'fr',
                '{fr_safe}',
                NULL,
                NULL,
                now(),
                now()
            FROM services s
            WHERE s.name = '{en_safe}'
            ON CONFLICT (service_id, language) DO UPDATE
                SET name = EXCLUDED.name, updated_at = now()
        """)


def downgrade() -> None:
    op.execute("DELETE FROM service_translations WHERE language = 'fr'")
    op.execute("DELETE FROM service_category_translations WHERE language = 'fr'")
