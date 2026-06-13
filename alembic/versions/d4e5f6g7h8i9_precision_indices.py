"""Add NDMI and biomasse to sc_indices_satellitaires

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sc_indices_satellitaires',
                  sa.Column('ndmi', sa.Float(), nullable=True))
    op.add_column('sc_indices_satellitaires',
                  sa.Column('biomasse', sa.Float(), nullable=True))
    op.add_column('sc_indices_satellitaires',
                  sa.Column('temperature_canopee', sa.Float(), nullable=True))
    op.add_column('sc_indices_satellitaires',
                  sa.Column('ndmi_label', sa.String(15), nullable=True))
    op.add_column('sc_indices_satellitaires',
                  sa.Column('biomasse_label', sa.String(15), nullable=True))


def downgrade():
    op.drop_column('sc_indices_satellitaires', 'biomasse_label')
    op.drop_column('sc_indices_satellitaires', 'ndmi_label')
    op.drop_column('sc_indices_satellitaires', 'temperature_canopee')
    op.drop_column('sc_indices_satellitaires', 'biomasse')
    op.drop_column('sc_indices_satellitaires', 'ndmi')
