"""wizard_champ_update — Module Mon Champ v2 — Wizard 12 étapes

Ajoute :
  champ_parcelles : source_eau_principale, type_irrigation,
                    etape_wizard, wizard_complet, date_activation
  champ_sols      : temperature_sol, humidite_sol, salinite,
                    source_analyse, analyse_satellite
  champ_infrastructures : photo_url, categorie, type → VARCHAR
  champ_sources_eau     : notes

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── champ_parcelles ────────────────────────────────────────────────────────
    op.add_column('champ_parcelles',
        sa.Column('source_eau_principale', sa.String(100), nullable=True))
    op.add_column('champ_parcelles',
        sa.Column('type_irrigation', sa.String(100), nullable=True))
    op.add_column('champ_parcelles',
        sa.Column('etape_wizard', sa.SmallInteger(), nullable=True, server_default='1'))
    op.add_column('champ_parcelles',
        sa.Column('wizard_complet', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('champ_parcelles',
        sa.Column('date_activation', sa.DateTime(timezone=True), nullable=True))

    # ── champ_sols ─────────────────────────────────────────────────────────────
    op.add_column('champ_sols',
        sa.Column('temperature_sol', sa.Float(), nullable=True))
    op.add_column('champ_sols',
        sa.Column('humidite_sol', sa.Float(), nullable=True))
    op.add_column('champ_sols',
        sa.Column('salinite', sa.Float(), nullable=True))
    op.add_column('champ_sols',
        sa.Column('source_analyse', sa.String(50), nullable=True))
    op.add_column('champ_sols',
        sa.Column('analyse_satellite', JSONB(), nullable=True))

    # ── champ_infrastructures ──────────────────────────────────────────────────
    op.add_column('champ_infrastructures',
        sa.Column('photo_url', sa.String(500), nullable=True))
    op.add_column('champ_infrastructures',
        sa.Column('categorie', sa.String(100), nullable=True))
    # Change type column from PostgreSQL enum to VARCHAR for extensibility
    op.execute(
        "ALTER TABLE champ_infrastructures "
        "ALTER COLUMN type TYPE VARCHAR(100) USING type::text"
    )
    op.execute("DROP TYPE IF EXISTS typeinfrastructure")

    # ── champ_sources_eau ──────────────────────────────────────────────────────
    op.add_column('champ_sources_eau',
        sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('champ_sources_eau', 'notes')
    op.drop_column('champ_infrastructures', 'categorie')
    op.drop_column('champ_infrastructures', 'photo_url')
    op.drop_column('champ_sols', 'analyse_satellite')
    op.drop_column('champ_sols', 'source_analyse')
    op.drop_column('champ_sols', 'salinite')
    op.drop_column('champ_sols', 'humidite_sol')
    op.drop_column('champ_sols', 'temperature_sol')
    op.drop_column('champ_parcelles', 'date_activation')
    op.drop_column('champ_parcelles', 'wizard_complet')
    op.drop_column('champ_parcelles', 'etape_wizard')
    op.drop_column('champ_parcelles', 'type_irrigation')
    op.drop_column('champ_parcelles', 'source_eau_principale')
