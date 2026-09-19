"""admin two-factor authentication (TOTP)

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("admins", sa.Column("totp_secret", sa.String(64), nullable=True), schema="hirely")
    op.add_column("admins", sa.Column("totp_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="hirely")
    op.add_column("admins", sa.Column("totp_last_step", sa.BigInteger(), nullable=True), schema="hirely")


def downgrade() -> None:
    for c in ("totp_last_step", "totp_enabled", "totp_secret"):
        op.drop_column("admins", c, schema="hirely")
