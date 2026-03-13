"""add ab_tests table

Revision ID: 005_add_ab_tests
Revises: (manual)
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "ab_tests",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500), server_default=""),
        sa.Column("variant_a_name", sa.String(50), server_default="A"),
        sa.Column("variant_b_name", sa.String(50), server_default="B"),
        sa.Column("variant_a_value", sa.Text, server_default=""),
        sa.Column("variant_b_value", sa.Text, server_default=""),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("ab_tests")
