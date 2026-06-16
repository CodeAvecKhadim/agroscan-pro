"""fix: add EN_CULTURE (uppercase) to statutparcelle enum

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-06-16

SQLAlchemy stocke les noms de membres d'enum (uppercase).
La migration précédente avait ajouté 'en_culture' (lowercase).
Cette migration ajoute 'EN_CULTURE' (uppercase) et migre les lignes existantes.
"""
from alembic import op

revision = 'h8i9j0k1l2m3'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ADD VALUE requiert un COMMIT séparé avant tout DML (contrainte PostgreSQL).
    # La migration du UPDATE est faite dans i9j0k1l2m3n4_migrate_en_culture_rows.
    op.execute("ALTER TYPE statutparcelle ADD VALUE IF NOT EXISTS 'EN_CULTURE'")


def downgrade() -> None:
    # PostgreSQL ne supporte pas DROP VALUE — migration irreversible
    op.execute("UPDATE champ_parcelles SET statut = 'ACTIVE' WHERE statut::text = 'EN_CULTURE'")
