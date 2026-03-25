"""Deduplicate users — keep highest id per telegram_id.

Revision ID: aa0000000001
Revises: ff0000000001
Create Date: 2026-03-25
"""
from alembic import op
from sqlalchemy import text

# revision identifiers
revision = "aa0000000001"
down_revision = "ff0000000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Count duplicates
    result = conn.execute(text("""
        SELECT COUNT(*) FROM users
        WHERE id NOT IN (
            SELECT MAX(id) FROM users GROUP BY telegram_id
        )
    """))
    dup_count = result.scalar()

    if dup_count == 0:
        print("✅ Dublikat foydalanuvchilar topilmadi — migration o'tkazib yuborildi.")
        return

    print(f"⚠️  {dup_count} ta dublikat foydalanuvchi topildi. Tozalanmoqda...")

    # 2. Remove FK-dependent rows first
    conn.execute(text("""
        DELETE FROM referral_balances
        WHERE user_id IN (
            SELECT id FROM users
            WHERE id NOT IN (SELECT MAX(id) FROM users GROUP BY telegram_id)
        )
    """))

    conn.execute(text("""
        DELETE FROM events
        WHERE user_id IN (
            SELECT id FROM users
            WHERE id NOT IN (SELECT MAX(id) FROM users GROUP BY telegram_id)
        )
    """))

    # Also clean payments tied to duplicate user ids (if any)
    conn.execute(text("""
        DELETE FROM payments
        WHERE user_id IN (
            SELECT id FROM users
            WHERE id NOT IN (SELECT MAX(id) FROM users GROUP BY telegram_id)
        )
    """))

    # 3. Delete duplicates, keep MAX(id) per telegram_id
    conn.execute(text("""
        DELETE FROM users
        WHERE id NOT IN (
            SELECT MAX(id) FROM users GROUP BY telegram_id
        )
    """))

    print(f"✅ {dup_count} ta dublikat o'chirildi!")


def downgrade() -> None:
    # Downgrade not possible — deleted rows cannot be restored
    pass
