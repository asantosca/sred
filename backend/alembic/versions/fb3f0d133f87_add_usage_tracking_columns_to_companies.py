"""Add usage tracking columns to companies

Revision ID: fb3f0d133f87
Revises: 5ea213ee766b
Create Date: 2025-11-08 22:06:14.864352

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb3f0d133f87'
down_revision = '5ea213ee766b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add usage tracking columns to companies table
    op.add_column('companies', sa.Column('usage_documents_count', sa.Integer(), server_default='0', nullable=False), schema='sred_ds')
    op.add_column('companies', sa.Column('usage_storage_bytes', sa.BigInteger(), server_default='0', nullable=False), schema='sred_ds')
    op.add_column('companies', sa.Column('usage_ai_queries_count', sa.Integer(), server_default='0', nullable=False), schema='sred_ds')
    op.add_column('companies', sa.Column('usage_embeddings_count', sa.Integer(), server_default='0', nullable=False), schema='sred_ds')
    op.add_column('companies', sa.Column('usage_reset_date', sa.Date(), nullable=True), schema='sred_ds')


def downgrade() -> None:
    op.drop_column('companies', 'usage_reset_date', schema='sred_ds')
    op.drop_column('companies', 'usage_embeddings_count', schema='sred_ds')
    op.drop_column('companies', 'usage_ai_queries_count', schema='sred_ds')
    op.drop_column('companies', 'usage_storage_bytes', schema='sred_ds')
    op.drop_column('companies', 'usage_documents_count', schema='sred_ds')