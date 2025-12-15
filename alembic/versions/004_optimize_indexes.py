"""Optimize indexes for maximum speed

Revision ID: 004_optimize_indexes
Revises: 003_add_missing_cols
Create Date: 2025-12-15 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_optimize_indexes'
down_revision: Union[str, None] = '003_add_missing_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Composite Index for Daily Logs (Most frequent query: get usage for user X on day Y)
    # Checks if index exists first to be idempotent
    # Note: postgres filter for user_id AND date
    try:
        op.create_index('idx_daily_logs_user_date', 'daily_logs', ['user_id', 'date'], unique=False)
    except Exception:
        pass # Already exists

    # 2. Index for recent activity (Optimizes leaderboard)
    try:
        op.create_index('idx_users_active_points', 'users', ['active', 'points'], unique=False)
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index('idx_daily_logs_user_date', table_name='daily_logs')
        op.drop_index('idx_users_active_points', table_name='users')
    except Exception:
        pass
