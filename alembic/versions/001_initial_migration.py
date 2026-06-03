"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-15 20:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotency Check
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # 1. Users
    if 'users' not in tables:
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('telegram_id', sa.BigInteger(), nullable=True),
            sa.Column('username', sa.String(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('phone', sa.String(), nullable=True),
            sa.Column('age', sa.Integer(), nullable=True),
            sa.Column('gender', sa.String(), nullable=True),
            sa.Column('height', sa.Integer(), nullable=True),
            sa.Column('weight', sa.Float(), nullable=True),
            sa.Column('target_weight', sa.Float(), nullable=True),
            sa.Column('goal', sa.String(), nullable=True),
            sa.Column('activity_level', sa.String(), nullable=True),
            sa.Column('allergies', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('is_premium', sa.Boolean(), nullable=True),
            sa.Column('premium_until', sa.DateTime(), nullable=True),
            sa.Column('points', sa.Integer(), nullable=True),
            sa.Column('referral_code', sa.String(), nullable=True),
            sa.Column('referrer_id', sa.Integer(), nullable=True),
            sa.Column('last_checkin', sa.String(), nullable=True),
            sa.Column('active', sa.Boolean(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('yasha_points', sa.Integer(), nullable=True),
            sa.Column('streak_water', sa.Integer(), nullable=True),
            sa.Column('streak_sleep', sa.Integer(), nullable=True),
            sa.Column('streak_mood', sa.Integer(), nullable=True),
            sa.Column('calorie_last_use_date', sa.String(), nullable=True),
            sa.Column('calorie_daily_uses', sa.Integer(), nullable=True),
            sa.Column('ai_menu_count', sa.Integer(), nullable=True),
            sa.Column('ai_workout_count', sa.Integer(), nullable=True),
            sa.Column('ai_last_reset_month', sa.String(), nullable=True),
            sa.Column('plan_type', sa.String(), nullable=True),
            sa.Column('daily_stats', sa.Text(), nullable=True),
            sa.Column('trial_start', sa.String(), nullable=True),
            sa.Column('trial_used', sa.Integer(), nullable=True),
            sa.Column('auto_renew', sa.Integer(), nullable=True),
            sa.Column('onboarding_state', sa.Integer(), nullable=True),
            sa.Column('onboarding_data', sa.Text(), nullable=True),
            sa.Column('utm_raw', sa.String(), nullable=True),
            sa.Column('utm_source', sa.String(), nullable=True),
            sa.Column('utm_campaign', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
        op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)
        op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
        op.create_foreign_key('fk_users_referrer', 'users', 'users', ['referrer_id'], ['id'])

    # 2. Daily Logs
    if 'daily_logs' not in tables:
        op.create_table('daily_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('date', sa.String(), nullable=True),
            sa.Column('water_drank', sa.Boolean(), nullable=True),
            sa.Column('workout_done', sa.Boolean(), nullable=True),
            sa.Column('steps_count', sa.Integer(), nullable=True),
            sa.Column('steps', sa.Integer(), nullable=True),
            sa.Column('calories_consumed', sa.Integer(), nullable=True),
            sa.Column('stages_reward_claimed', sa.Boolean(), nullable=True),
            sa.Column('steps_reward_claimed', sa.Boolean(), nullable=True),
            sa.Column('water_ml', sa.Integer(), nullable=True),
            sa.Column('sleep_hours', sa.Float(), nullable=True),
            sa.Column('mood', sa.String(), nullable=True),
            sa.Column('mood_reason', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_daily_logs_date'), 'daily_logs', ['date'], unique=False)
        op.create_index(op.f('ix_daily_logs_id'), 'daily_logs', ['id'], unique=False)

    # 3. Plans
    if 'plans' not in tables:
        op.create_table('plans',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('type', sa.String(), nullable=True),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_plans_id'), 'plans', ['id'], unique=False)

    # 4. Transactions
    if 'transactions' not in tables:
        op.create_table('transactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(), nullable=True),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)

    # 5. Feedback
    if 'feedback' not in tables:
        op.create_table('feedback',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)

    # 6. Orders
    if 'orders' not in tables:
        op.create_table('orders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.String(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('days', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
        op.create_index(op.f('ix_orders_order_id'), 'orders', ['order_id'], unique=True)

    # 7. Activity Logs
    if 'activity_logs' not in tables:
        op.create_table('activity_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('type', sa.String(), nullable=True),
            sa.Column('payload', sa.Text(), nullable=True),
            sa.Column('ts', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_activity_logs_id'), 'activity_logs', ['id'], unique=False)

    # 8. Calorie Logs
    if 'calorie_logs' not in tables:
        op.create_table('calorie_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('total_kcal', sa.Integer(), nullable=True),
            sa.Column('json_data', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_calorie_logs_id'), 'calorie_logs', ['id'], unique=False)

    # 9. Menu Templates
    if 'menu_templates' not in tables:
        op.create_table('menu_templates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('profile_key', sa.String(), nullable=True),
            sa.Column('menu_json', sa.Text(), nullable=True),
            sa.Column('shopping_list_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_menu_templates_id'), 'menu_templates', ['id'], unique=False)
        op.create_index(op.f('ix_menu_templates_profile_key'), 'menu_templates', ['profile_key'], unique=True)

    # 10. User Menu Links
    if 'user_menu_links' not in tables:
        op.create_table('user_menu_links',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('menu_template_id', sa.Integer(), nullable=True),
            sa.Column('start_date', sa.DateTime(), nullable=True),
            sa.Column('current_day_index', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['menu_template_id'], ['menu_templates.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_menu_links_id'), 'user_menu_links', ['id'], unique=False)

    # 11. Workout Templates
    if 'workout_templates' not in tables:
        op.create_table('workout_templates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('profile_key', sa.String(), nullable=True),
            sa.Column('workout_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workout_templates_id'), 'workout_templates', ['id'], unique=False)
        op.create_index(op.f('ix_workout_templates_profile_key'), 'workout_templates', ['profile_key'], unique=True)

    # 12. User Workout Links
    if 'user_workout_links' not in tables:
        op.create_table('user_workout_links',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('workout_template_id', sa.Integer(), nullable=True),
            sa.Column('start_date', sa.DateTime(), nullable=True),
            sa.Column('current_day_index', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['workout_template_id'], ['workout_templates.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_workout_links_id'), 'user_workout_links', ['id'], unique=False)

    # 13. Workout Cache
    if 'workout_cache' not in tables:
        op.create_table('workout_cache',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('plan_text', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workout_cache_id'), 'workout_cache', ['id'], unique=False)

    # 14. Menu Cache
    if 'menu_cache' not in tables:
        op.create_table('menu_cache',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('menu_text', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_menu_cache_id'), 'menu_cache', ['id'], unique=False)

    # 15. Admin Logs
    if 'admin_logs' not in tables:
        op.create_table('admin_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('admin_id', sa.BigInteger(), nullable=True),
            sa.Column('action', sa.String(), nullable=True),
            sa.Column('target_id', sa.BigInteger(), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_admin_logs_id'), 'admin_logs', ['id'], unique=False)

    # 16. Bot Content
    if 'bot_content' not in tables:
        op.create_table('bot_content',
            sa.Column('key', sa.String(), nullable=False),
            sa.Column('value', sa.Text(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('key')
        )

    # 17. Exercises (Placeholder for migration compatibility)
    if 'exercises' not in tables:
        op.create_table('exercises',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

    # 18. Subscriptions
    if 'subscriptions' not in tables:
        op.create_table('subscriptions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='inactive'),
            sa.Column('plan', sa.String(length=30), nullable=True, server_default='monthly'),
            sa.Column('price', sa.Integer(), nullable=False),
            sa.Column('card_token', sa.String(length=255), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('cancelled_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )

    # 19. Referrals
    if 'referrals' not in tables:
        op.create_table('referrals',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('referer_id', sa.BigInteger(), nullable=False),
            sa.Column('referred_id', sa.BigInteger(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
            sa.Column('reward_amount', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('phone_hash', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column('validated_at', sa.DateTime(), nullable=True),
            sa.Column('paid_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['referer_id'], ['users.telegram_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['referred_id'], ['users.telegram_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('referred_id')
        )
        op.create_index(op.f('ix_referrals_referer_id'), 'referrals', ['referer_id'], unique=False)

    # 20. Referral Balances
    if 'referral_balances' not in tables:
        op.create_table('referral_balances',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('balance', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('total_earned', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('total_used', sa.Integer(), nullable=True, server_default='0'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )

    # 21. Events
    if 'events' not in tables:
        op.create_table('events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('payload', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_events_event_type', 'events', ['event_type'], unique=False)
        op.create_index('ix_events_user_created', 'events', ['user_id', 'created_at'], unique=False)

    # 22. Lead Magnets
    if 'lead_magnets' not in tables:
        op.create_table('lead_magnets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('campaign', sa.String(length=100), nullable=False),
            sa.Column('content_type', sa.String(length=30), nullable=False),
            sa.Column('file_id', sa.String(length=255), nullable=True),
            sa.Column('file_url', sa.Text(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('campaign')
        )

    # 23. VSL Content
    if 'vsl_content' not in tables:
        op.create_table('vsl_content',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('level_tag', sa.String(length=20), nullable=False),
            sa.Column('goal_tag', sa.String(length=30), nullable=True),
            sa.Column('video_file_id', sa.String(length=255), nullable=True),
            sa.Column('video_url', sa.Text(), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_vsl_segment', 'vsl_content', ['level_tag', 'goal_tag'], unique=False)

    # 24. Course Modules
    if 'course_modules' not in tables:
        op.create_table('course_modules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('video_url', sa.Text(), nullable=True),
            sa.Column('video_file_id', sa.String(length=255), nullable=True),
            sa.Column('channel_message_id', sa.Integer(), nullable=True),
            sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('unlock_condition', sa.String(length=100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 25. User Progress
    if 'user_progress' not in tables:
        op.create_table('user_progress',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('module_id', sa.Integer(), nullable=False),
            sa.Column('watch_time', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('completion_pct', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'module_id', name='uq_user_module')
        )

    # 26. Payments
    if 'payments' not in tables:
        op.create_table('payments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Integer(), nullable=False),
            sa.Column('referral_discount', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('provider', sa.String(length=30), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
            sa.Column('transaction_id', sa.String(length=255), nullable=True),
            sa.Column('webhook_data', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)

    # 27. Broadcast Messages
    if 'broadcast_messages' not in tables:
        op.create_table('broadcast_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('filters', sa.JSON(), nullable=True),
            sa.Column('content_type', sa.String(length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('entities', sa.JSON(), nullable=True),
            sa.Column('file_id', sa.String(length=255), nullable=True),
            sa.Column('sent_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('failed_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('total_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='draft'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 28. Admin Settings
    if 'admin_settings' not in tables:
        op.create_table('admin_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('key', sa.String(length=100), nullable=False),
            sa.Column('value', sa.Text(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key')
        )

    # 29. Guides
    if 'guides' not in tables:
        op.create_table('guides',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('file_id', sa.String(length=255), nullable=True),
            sa.Column('file_type', sa.String(length=50), nullable=True),
            sa.Column('media_url', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('order', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 30. Scheduled Messages
    if 'scheduled_messages' not in tables:
        op.create_table('scheduled_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('content_type', sa.String(length=20), nullable=True, server_default='text'),
            sa.Column('file_id', sa.String(length=255), nullable=True),
            sa.Column('filters', sa.JSON(), nullable=True),
            sa.Column('send_at', sa.DateTime(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
            sa.Column('sent_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('failed_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 31. Job Vacancies
    if 'job_vacancies' not in tables:
        op.create_table('job_vacancies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('company', sa.String(length=255), nullable=True),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('salary', sa.String(length=100), nullable=True),
            sa.Column('job_type', sa.String(length=50), nullable=True, server_default='full_time'),
            sa.Column('location', sa.String(length=255), nullable=True),
            sa.Column('contact_info', sa.String(length=255), nullable=True),
            sa.Column('channel_msg_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
            sa.Column('submitted_by', sa.BigInteger(), nullable=False),
            sa.Column('reviewed_by', sa.BigInteger(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 32. Moderated Groups
    if 'moderated_groups' not in tables:
        op.create_table('moderated_groups',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('group_id', sa.BigInteger(), nullable=False),
            sa.Column('group_title', sa.String(length=255), nullable=True),
            sa.Column('added_by', sa.BigInteger(), nullable=False),
            sa.Column('anti_spam', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('bad_words_filter', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('captcha_enabled', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('flood_limit', sa.Integer(), nullable=True, server_default='10'),
            sa.Column('night_mode', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('night_start', sa.String(length=5), nullable=True, server_default='00:00'),
            sa.Column('night_end', sa.String(length=5), nullable=True, server_default='08:00'),
            sa.Column('welcome_message', sa.Text(), nullable=True),
            sa.Column('warn_limit', sa.Integer(), nullable=True, server_default='3'),
            sa.Column('plan', sa.String(length=10), nullable=True, server_default='free'),
            sa.Column('plan_expires_at', sa.DateTime(), nullable=True),
            sa.Column('last_ad_sent_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_moderated_groups_group_id'), 'moderated_groups', ['group_id'], unique=True)

    # 33. Banned Words
    if 'banned_words' not in tables:
        op.create_table('banned_words',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('group_id', sa.BigInteger(), nullable=False),
            sa.Column('word', sa.String(length=255), nullable=False),
            sa.Column('added_by', sa.BigInteger(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('group_id', 'word', name='uq_group_word')
        )
        op.create_index(op.f('ix_banned_words_group_id'), 'banned_words', ['group_id'], unique=False)

    # 34. Group Warnings
    if 'group_warnings' not in tables:
        op.create_table('group_warnings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('group_id', sa.BigInteger(), nullable=False),
            sa.Column('user_id', sa.BigInteger(), nullable=False),
            sa.Column('warned_by', sa.BigInteger(), nullable=False),
            sa.Column('reason', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_group_warnings_group_id'), 'group_warnings', ['group_id'], unique=False)
        op.create_index(op.f('ix_group_warnings_user_id'), 'group_warnings', ['user_id'], unique=False)

    # 35. Captcha Verifications
    if 'captcha_verifications' not in tables:
        op.create_table('captcha_verifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('group_id', sa.BigInteger(), nullable=False),
            sa.Column('user_id', sa.BigInteger(), nullable=False),
            sa.Column('verified', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('group_id', 'user_id', name='uq_captcha_group_user')
        )
        op.create_index(op.f('ix_captcha_verifications_group_id'), 'captcha_verifications', ['group_id'], unique=False)
        op.create_index(op.f('ix_captcha_verifications_user_id'), 'captcha_verifications', ['user_id'], unique=False)

    # 36. Admin Users
    if 'admin_users' not in tables:
        op.create_table('admin_users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=False, server_default='admin'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_admin_users_username'), 'admin_users', ['username'], unique=True)

def downgrade() -> None:
    # Reverse order
    op.drop_index(op.f('ix_admin_users_username'), table_name='admin_users')
    op.drop_table('admin_users')
    op.drop_index(op.f('ix_captcha_verifications_user_id'), table_name='captcha_verifications')
    op.drop_index(op.f('ix_captcha_verifications_group_id'), table_name='captcha_verifications')
    op.drop_table('captcha_verifications')
    op.drop_index(op.f('ix_group_warnings_user_id'), table_name='group_warnings')
    op.drop_index(op.f('ix_group_warnings_group_id'), table_name='group_warnings')
    op.drop_table('group_warnings')
    op.drop_index(op.f('ix_banned_words_group_id'), table_name='banned_words')
    op.drop_table('banned_words')
    op.drop_index(op.f('ix_moderated_groups_group_id'), table_name='moderated_groups')
    op.drop_table('moderated_groups')
    op.drop_table('job_vacancies')
    op.drop_table('scheduled_messages')
    op.drop_table('guides')
    op.drop_table('admin_settings')
    op.drop_table('broadcast_messages')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_table('payments')
    op.drop_table('user_progress')
    op.drop_table('course_modules')
    op.drop_index('ix_vsl_segment', table_name='vsl_content')
    op.drop_table('vsl_content')
    op.drop_table('lead_magnets')
    op.drop_index('ix_events_user_created', table_name='events')
    op.drop_index('ix_events_event_type', table_name='events')
    op.drop_table('events')
    op.drop_table('referral_balances')
    op.drop_index(op.f('ix_referrals_referer_id'), table_name='referrals')
    op.drop_table('referrals')
    op.drop_table('subscriptions')
    # Reverse order
    op.drop_table('exercises')
    op.drop_table('bot_content')
    op.drop_index(op.f('ix_admin_logs_id'), table_name='admin_logs')
    op.drop_table('admin_logs')
    op.drop_index(op.f('ix_menu_cache_id'), table_name='menu_cache')
    op.drop_table('menu_cache')
    op.drop_index(op.f('ix_workout_cache_id'), table_name='workout_cache')
    op.drop_table('workout_cache')
    op.drop_index(op.f('ix_user_workout_links_id'), table_name='user_workout_links')
    op.drop_table('user_workout_links')
    op.drop_index(op.f('ix_workout_templates_profile_key'), table_name='workout_templates')
    op.drop_index(op.f('ix_workout_templates_id'), table_name='workout_templates')
    op.drop_table('workout_templates')
    op.drop_index(op.f('ix_user_menu_links_id'), table_name='user_menu_links')
    op.drop_table('user_menu_links')
    op.drop_index(op.f('ix_menu_templates_profile_key'), table_name='menu_templates')
    op.drop_index(op.f('ix_menu_templates_id'), table_name='menu_templates')
    op.drop_table('menu_templates')
    op.drop_index(op.f('ix_calorie_logs_id'), table_name='calorie_logs')
    op.drop_table('calorie_logs')
    op.drop_index(op.f('ix_activity_logs_id'), table_name='activity_logs')
    op.drop_table('activity_logs')
    op.drop_index(op.f('ix_orders_order_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')
    op.drop_index(op.f('ix_feedback_id'), table_name='feedback')
    op.drop_table('feedback')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_plans_id'), table_name='plans')
    op.drop_table('plans')
    op.drop_index(op.f('ix_daily_logs_id'), table_name='daily_logs')
    op.drop_index(op.f('ix_daily_logs_date'), table_name='daily_logs')
    op.drop_table('daily_logs')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
