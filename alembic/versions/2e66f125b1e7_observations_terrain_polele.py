"""observations_terrain_polele

Revision ID: 2e66f125b1e7
Revises: h8i9j0k1l2m3
Create Date: 2026-06-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '2e66f125b1e7'
down_revision: Union[str, Sequence[str], None] = 'h8i9j0k1l2m3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'observations_terrain',
        sa.Column('id',                    sa.Integer(),     primary_key=True),
        sa.Column('org_id',                sa.Integer(),     sa.ForeignKey('organizations.id',   ondelete='CASCADE'), nullable=False),
        sa.Column('parcelle_id',           sa.Integer(),     sa.ForeignKey('champ_parcelles.id', ondelete='CASCADE'), nullable=True),
        sa.Column('user_id',               sa.Integer(),     sa.ForeignKey('users.id',           ondelete='SET NULL'), nullable=True),
        sa.Column('date_observation',      sa.Date(),        nullable=False),
        sa.Column('irrigation_effectuee',  sa.Boolean(),     nullable=True),
        sa.Column('pluie_observee',        sa.Boolean(),     nullable=True),
        sa.Column('etat_feuilles',         sa.String(30),    nullable=True),
        sa.Column('ravageurs_observes',    sa.Boolean(),     nullable=True),
        sa.Column('maladie_observee',      sa.Boolean(),     nullable=True),
        sa.Column('confiance_observation', sa.String(10),    nullable=True),
        sa.Column('notes',                 sa.Text(),        nullable=True),
        sa.Column('created_at',            sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_obs_terrain_org',      'observations_terrain', ['org_id'])
    op.create_index('ix_obs_terrain_parcelle', 'observations_terrain', ['parcelle_id'])
    op.create_index('ix_obs_terrain_date',     'observations_terrain', ['date_observation'])


def downgrade() -> None:
    op.drop_index('ix_obs_terrain_date',     table_name='observations_terrain')
    op.drop_index('ix_obs_terrain_parcelle', table_name='observations_terrain')
    op.drop_index('ix_obs_terrain_org',      table_name='observations_terrain')
    op.drop_table('observations_terrain')
