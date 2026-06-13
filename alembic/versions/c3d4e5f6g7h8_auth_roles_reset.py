"""auth_roles_reset — M1 Auth : nouveaux rôles + colonnes reset/vérification

Ajoute :
  users : reset_token, reset_token_expires, email_verified,
          email_verification_token, phone_verified, phone_otp, phone_otp_expires
  userrole enum : conseiller, producteur, technicien, laboratoire, super_admin

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Ajouter nouveaux rôles à l'enum PostgreSQL ────────────────────────
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'conseiller'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'producteur'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'technicien'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'laboratoire'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'super_admin'")

    # ── 2. Colonnes reset mot de passe ───────────────────────────────────────
    op.add_column('users', sa.Column('reset_token', sa.String(128), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True))

    # ── 3. Vérification email ────────────────────────────────────────────────
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('email_verification_token', sa.String(128), nullable=True))

    # ── 4. Vérification téléphone / OTP ─────────────────────────────────────
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('phone_otp', sa.String(8), nullable=True))
    op.add_column('users', sa.Column('phone_otp_expires', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'phone_otp_expires')
    op.drop_column('users', 'phone_otp')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')
    # Note: PostgreSQL ne permet pas de retirer une valeur d'enum facilement
