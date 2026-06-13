"""phone mandatory, email optional

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-06-13

Changements :
  - users.email : DROP NOT NULL (devient facultatif)
  - users.phone : CREATE UNIQUE INDEX partiel (WHERE phone IS NOT NULL)
  - users.phone : CREATE INDEX simple (pour les lookups)
"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6g7h8i9j0'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Rendre email facultatif
    op.alter_column('users', 'email',
                    existing_type=sa.String(),
                    nullable=True)

    # 2. Index unique partiel sur phone (ignore les NULL → comptes legacy sans téléphone)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_unique
        ON users (
            regexp_replace(regexp_replace(phone, ' ', '', 'g'), '-', '', 'g')
        )
        WHERE phone IS NOT NULL
    """)

    # 3. Index simple sur phone (si pas déjà présent via le modèle)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_phone
        ON users (phone)
        WHERE phone IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_phone_unique")
    op.execute("DROP INDEX IF EXISTS ix_users_phone")
    op.alter_column('users', 'email',
                    existing_type=sa.String(),
                    nullable=False)
