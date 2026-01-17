"""add api_usage_logs table

Revision ID: 7af4d1da845f
Revises: 5a47b5df3f00
Create Date: 2025-12-16 17:12:24.472325

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '7af4d1da845f'
down_revision = '5a47b5df3f00'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'api_usage_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('sred_ds.companies.id'), nullable=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('sred_ds.users.id'), nullable=True),
        sa.Column('service', sa.String(50), nullable=False),
        sa.Column('operation', sa.String(100), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('pages_processed', sa.Integer(), nullable=True),
        sa.Column('chunks_processed', sa.Integer(), nullable=True),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('estimated_cost_cents', sa.Integer(), nullable=True),
        sa.Column('document_id', UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='sred_ds'
    )

    # Create indexes for common query patterns
    op.create_index(
        'ix_api_usage_logs_company_id',
        'api_usage_logs',
        ['company_id'],
        schema='sred_ds'
    )
    op.create_index(
        'ix_api_usage_logs_service',
        'api_usage_logs',
        ['service'],
        schema='sred_ds'
    )
    op.create_index(
        'ix_api_usage_logs_created_at',
        'api_usage_logs',
        ['created_at'],
        schema='sred_ds'
    )


def downgrade() -> None:
    op.drop_index('ix_api_usage_logs_created_at', table_name='api_usage_logs', schema='sred_ds')
    op.drop_index('ix_api_usage_logs_service', table_name='api_usage_logs', schema='sred_ds')
    op.drop_index('ix_api_usage_logs_company_id', table_name='api_usage_logs', schema='sred_ds')
    op.drop_table('api_usage_logs', schema='sred_ds')