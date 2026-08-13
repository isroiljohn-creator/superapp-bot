"""add is_team_member to users (fixes preexisting column drift)

Revision ID: b1000000001
Revises: 5819cbc5a6e7
Create Date: 2026-08-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1000000001'
down_revision = '5819cbc5a6e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('is_team_member', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('users', 'is_team_member')
