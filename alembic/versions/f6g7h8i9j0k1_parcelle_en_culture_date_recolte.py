"""parcelle: statut EN_CULTURE + date_recolte_prevue

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-06-16

Changements :
  - Ajoute la valeur 'en_culture' dans l'enum statut de champ_parcelles
  - Ajoute la colonne date_recolte_prevue (DATE nullable) à champ_parcelles
"""
from alembic import op
import sqlalchemy as sa

revision = 'f6g7h8i9j0k1'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Ajouter la valeur 'en_culture' à l'enum PostgreSQL
    op.execute("ALTER TYPE statutparcelle ADD VALUE IF NOT EXISTS 'en_culture'")

    # 2. Ajouter la colonne date_recolte_prevue
    op.add_column(
        'champ_parcelles',
        sa.Column('date_recolte_prevue', sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('champ_parcelles', 'date_recolte_prevue')
    # Note : PostgreSQL ne supporte pas DROP VALUE sur un enum — pas de rollback enum possible.
