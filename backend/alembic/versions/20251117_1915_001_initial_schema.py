"""Initial schema with user budgets

Revision ID: 001
Revises:
Create Date: 2025-11-17 19:15:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('monthly_budget_aud', sa.Numeric(10, 2), nullable=False, server_default='5000.00'),
        sa.Column('current_spend_aud', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('settings', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_departments_name', 'departments', ['name'])

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('azure_ad_id', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('department_id', sa.String(36), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('role', sa.Enum('SUPER_ADMIN', 'ORG_ADMIN', 'DEPARTMENT_MANAGER', 'POWER_USER', 'STANDARD_USER', name='userrole'), nullable=False, server_default='STANDARD_USER'),
        sa.Column('settings', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_users_azure_ad_id', 'users', ['azure_ad_id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_department_id', 'users', ['department_id'])
    op.create_index('ix_users_role', 'users', ['role'])

    # Create user_budgets table
    op.create_table(
        'user_budgets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('monthly_budget_aud', sa.Numeric(10, 2), nullable=False),
        sa.Column('current_spend_aud', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('budget_period_year', sa.Integer, nullable=False),
        sa.Column('budget_period_month', sa.Integer, nullable=False),
        sa.Column('alert_threshold_percent', sa.Integer, nullable=False, server_default='80'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('set_by_user_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_user_budgets_user_id', 'user_budgets', ['user_id'])
    op.create_index('ix_user_budgets_budget_period_year', 'user_budgets', ['budget_period_year'])
    op.create_index('ix_user_budgets_budget_period_month', 'user_budgets', ['budget_period_month'])

    # Create generations table
    op.create_table(
        'generations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prompt', sa.Text, nullable=False),
        sa.Column('negative_prompt', sa.Text, nullable=True),
        sa.Column('model_used', sa.Enum('DALLE3', 'SDXL', 'FIREFLY', 'AZURE_AI', name='modeltype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED', name='generationstatus'), nullable=False, server_default='PENDING'),
        sa.Column('image_url', sa.String(1024), nullable=True),
        sa.Column('thumbnail_url', sa.String(1024), nullable=True),
        sa.Column('cost_aud', sa.Numeric(10, 4), nullable=False),
        sa.Column('generation_time_ms', sa.Integer, nullable=True),
        sa.Column('metadata', sa.String, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_generations_user_id', 'generations', ['user_id'])
    op.create_index('ix_generations_model_used', 'generations', ['model_used'])
    op.create_index('ix_generations_status', 'generations', ['status'])
    op.create_index('ix_generations_created_at', 'generations', ['created_at'])


def downgrade() -> None:
    op.drop_table('generations')
    op.drop_table('user_budgets')
    op.drop_table('users')
    op.drop_table('departments')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS generationstatus')
    op.execute('DROP TYPE IF EXISTS modeltype')
    op.execute('DROP TYPE IF EXISTS userrole')
