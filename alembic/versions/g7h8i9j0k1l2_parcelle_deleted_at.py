"""parcelle: ajout colonne deleted_at pour suppression logique

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-06-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'g7h8i9j0k1l2'
down_revision = 'f6g7h8i9j0k1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'champ_parcelles',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    # Rétro-remplir deleted_at pour les parcelles déjà archivées
    op.execute("""
        UPDATE champ_parcelles
        SET deleted_at = updated_at
        WHERE statut = 'ARCHIVE' AND deleted_at IS NULL
    """)


def downgrade() -> None:
    op.drop_column('champ_parcelles', 'deleted_at')
