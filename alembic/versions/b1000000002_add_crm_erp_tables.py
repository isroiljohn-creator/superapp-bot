"""add CRM/ERP tables: products, purchases, applications, deals, deal_notes, deal_tasks, expenses

Revision ID: b1000000002
Revises: b1000000001
Create Date: 2026-08-13 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1000000002'
down_revision = 'b1000000001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    op.create_table(
        'purchases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('telegram_charge_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_purchases_status', 'purchases', ['status'], unique=False)
    op.create_index('ix_purchases_user_product', 'purchases', ['user_id', 'product_id'], unique=False)
    op.create_index(op.f('ix_purchases_user_id'), 'purchases', ['user_id'], unique=False)

    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('answers', sa.JSON(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tier', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_applications_tier', 'applications', ['tier'], unique=False)
    op.create_index(op.f('ix_applications_user_id'), 'applications', ['user_id'], unique=False)

    op.create_table(
        'deals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=30), nullable=False, server_default='new'),
        sa.Column('amount', sa.Integer(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('lost_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['assigned_to'], ['admin_users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deals_stage', 'deals', ['stage'], unique=False)
    op.create_index(op.f('ix_deals_user_id'), 'deals', ['user_id'], unique=False)
    op.create_index(op.f('ix_deals_assigned_to'), 'deals', ['assigned_to'], unique=False)

    op.create_table(
        'deal_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_deal_notes_deal_id'), 'deal_notes', ['deal_id'], unique=False)

    op.create_table(
        'deal_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('task_type', sa.String(length=20), nullable=False, server_default='task'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deal_tasks_status', 'deal_tasks', ['status'], unique=False)
    op.create_index('ix_deal_tasks_due_at', 'deal_tasks', ['due_at'], unique=False)
    op.create_index(op.f('ix_deal_tasks_deal_id'), 'deal_tasks', ['deal_id'], unique=False)

    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('expense_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_expenses_date', 'expenses', ['expense_date'], unique=False)
    op.create_index('ix_expenses_category', 'expenses', ['category'], unique=False)

    # Seed the product catalog
    products_table = sa.table(
        'products',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('price', sa.Integer),
        sa.column('is_active', sa.Boolean),
    )
    op.bulk_insert(
        products_table,
        [
            {'code': 'tripwire_ai_start', 'name': "AI START — 90 daqiqalik amaliy intensiv", 'price': 149_000, 'is_active': True},
            {'code': 'full_course', 'name': "To'liq kurs", 'price': 4_000_000, 'is_active': True},
            {'code': 'club_legacy', 'name': "Yopiq Klub (eski obuna, endi sotilmaydi)", 'price': 97_000, 'is_active': False},
        ],
    )


def downgrade() -> None:
    op.drop_table('expenses')
    op.drop_table('deal_tasks')
    op.drop_table('deal_notes')
    op.drop_table('deals')
    op.drop_table('applications')
    op.drop_table('purchases')
    op.drop_table('products')
