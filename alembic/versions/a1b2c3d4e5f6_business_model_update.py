"""business_model_update — nouveau modèle économique juin 2026

Ajoute :
  subscriptions.campaign_billing
  usage_counters.daily_ai_count
  usage_counters.daily_ai_date
  usage_counters.weekly_satellite_count
  usage_counters.weekly_period

Revision ID: a1b2c3d4e5f6
Revises: 753ff656feea
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '753ff656feea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # subscriptions : type de facturation (mensuel/annuel) pour coopérative
    op.add_column('subscriptions',
        sa.Column('campaign_billing', sa.String(), nullable=True, server_default='monthly'))

    # usage_counters : suivi journalier IA
    op.add_column('usage_counters',
        sa.Column('daily_ai_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('usage_counters',
        sa.Column('daily_ai_date', sa.String(), nullable=True))

    # usage_counters : suivi hebdomadaire satellite
    op.add_column('usage_counters',
        sa.Column('weekly_satellite_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('usage_counters',
        sa.Column('weekly_period', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('usage_counters', 'weekly_period')
    op.drop_column('usage_counters', 'weekly_satellite_count')
    op.drop_column('usage_counters', 'daily_ai_date')
    op.drop_column('usage_counters', 'daily_ai_count')
    op.drop_column('subscriptions', 'campaign_billing')
