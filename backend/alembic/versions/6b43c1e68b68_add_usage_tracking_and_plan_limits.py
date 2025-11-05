"""Add usage tracking and plan limits

Revision ID: 6b43c1e68b68
Revises: 7fd19330d81e
Create Date: 2025-11-05 00:28:04.154267

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '6b43c1e68b68'
down_revision = '7fd19330d81e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add usage tracking columns to companies table
    op.add_column('companies', sa.Column('usage_documents_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('companies', sa.Column('usage_storage_bytes', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('companies', sa.Column('usage_ai_queries_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('companies', sa.Column('usage_embeddings_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('companies', sa.Column('usage_reset_date', sa.Date(), nullable=True))

    # Create plan_limits table
    op.create_table(
        'plan_limits',
        sa.Column('plan_tier', sa.String(50), primary_key=True),
        sa.Column('max_documents', sa.Integer(), nullable=False, comment='Maximum documents allowed (-1 = unlimited)'),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False, comment='Maximum storage in GB (-1 = unlimited)'),
        sa.Column('max_ai_queries_per_month', sa.Integer(), nullable=False, comment='Maximum AI queries per month (-1 = unlimited)'),
        sa.Column('max_document_size_mb', sa.Integer(), nullable=False, comment='Maximum single document size in MB'),
        sa.Column('max_users', sa.Integer(), nullable=False, comment='Maximum users allowed (-1 = unlimited)'),
        sa.Column('allow_embeddings', sa.Boolean(), nullable=False, server_default='true', comment='Allow embedding generation'),
        sa.Column('allow_ocr', sa.Boolean(), nullable=False, server_default='false', comment='Allow OCR for scanned documents'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True)
    )

    # Insert default plan limits (conservative for beta/development)
    op.execute("""
        INSERT INTO plan_limits (
            plan_tier,
            max_documents,
            max_storage_gb,
            max_ai_queries_per_month,
            max_document_size_mb,
            max_users,
            allow_embeddings,
            allow_ocr
        ) VALUES
        ('free', 50, 1, 100, 10, 1, true, false),
        ('starter', 500, 10, 1000, 50, 5, true, false),
        ('professional', 5000, 100, 10000, 50, 25, true, true),
        ('enterprise', -1, -1, -1, 100, -1, true, true)
    """)

    # Create index for faster lookups
    op.create_index('idx_usage_tracking', 'companies', ['usage_documents_count', 'usage_storage_bytes', 'usage_ai_queries_count'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_usage_tracking', table_name='companies')

    # Drop plan_limits table
    op.drop_table('plan_limits')

    # Remove usage tracking columns from companies
    op.drop_column('companies', 'usage_reset_date')
    op.drop_column('companies', 'usage_embeddings_count')
    op.drop_column('companies', 'usage_ai_queries_count')
    op.drop_column('companies', 'usage_storage_bytes')
    op.drop_column('companies', 'usage_documents_count')