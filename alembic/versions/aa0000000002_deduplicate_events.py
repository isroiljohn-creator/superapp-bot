"""Deduplicate Events table — keep only first occurrence per (user_id, event_type).

Old race condition tracked `lead` and `registration_complete` events multiple
times per user. This migration removes the duplicates, keeping only the
earliest event for each (user_id, event_type) pair.
"""
from alembic import op
import sqlalchemy as sa

revision = 'aa0000000002'
down_revision = 'aa0000000001'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DELETE FROM events
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM events
            GROUP BY user_id, event_type
        )
    """)


def downgrade():
    pass  # Non-reversible — data is gone
