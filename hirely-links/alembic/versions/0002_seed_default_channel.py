"""seed the first channel (Hirely UZ Telegram channel)

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO hirely.channels (code, prefix, name, market, platform, external_ref) "
        "VALUES ('hirely_uz', 'UZ', 'Hirely UZ', 'uz', 'telegram', '@HirelyUz') ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DELETE FROM hirely.channels WHERE code = 'hirely_uz'")
