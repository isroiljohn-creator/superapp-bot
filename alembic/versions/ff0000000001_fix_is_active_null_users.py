"""fix: set is_active=TRUE for all NULL/FALSE users (broadcast fix)

Revision ID: ff0000000001
Revises: fe1234567890
Create Date: 2026-03-23 21:00:00.000000

Problem: Users created before is_active column was added had NULL or no value.
This migration sets is_active=TRUE for all users who are not explicitly blocked,
so broadcasts reach all legitimate users.

Safe rule: Only users marked FALSE by the lifecycle handler (bot blocked)
should stay FALSE. Everyone else → TRUE.
"""
from alembic import op
import sqlalchemy as sa

revision = 'ff0000000001'
down_revision = 'fe1234567890'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Ensure column exists and has NOT NULL + DEFAULT
    conn = op.get_bind()
    from sqlalchemy.engine.reflection import Inspector
    inspector = Inspector.from_engine(conn)
    columns = {col['name']: col for col in inspector.get_columns('users')}

    if 'is_active' in columns:
        # Update NULL values to TRUE (these are users who never blocked the bot)
        op.execute("UPDATE users SET is_active = TRUE WHERE is_active IS NULL")
        # Ensure column is NOT NULL with default
        op.execute("ALTER TABLE users ALTER COLUMN is_active SET DEFAULT TRUE")
        op.execute("ALTER TABLE users ALTER COLUMN is_active SET NOT NULL")
    else:
        # Column doesn't exist at all — add it
        op.add_column('users', sa.Column(
            'is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False
        ))
        op.execute("UPDATE users SET is_active = TRUE WHERE is_active IS NULL")


def downgrade() -> None:
    # Nothing to revert — setting NULL to TRUE is safe
    pass
