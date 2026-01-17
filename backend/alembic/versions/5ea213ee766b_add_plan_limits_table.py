"""Add plan_limits table

Revision ID: 5ea213ee766b
Revises: 7e84499ef797
Create Date: 2025-11-08 21:57:51.437282

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ea213ee766b'
down_revision = '7e84499ef797'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create plan_limits table
    op.create_table(
        'plan_limits',
        sa.Column('plan_tier', sa.String(50), primary_key=True),
        sa.Column('max_documents', sa.Integer(), nullable=False),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False),
        sa.Column('max_document_size_mb', sa.Integer(), nullable=False),
        sa.Column('max_users', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='sred_ds'
    )

    # Insert default plan tier limits
    op.execute("""
        INSERT INTO sred_ds.plan_limits (plan_tier, max_documents, max_storage_gb, max_document_size_mb, max_users)
        VALUES
            ('free', 100, 5, 10, 3),
            ('basic', 1000, 50, 50, 10),
            ('professional', 10000, 500, 100, 50),
            ('enterprise', -1, -1, 500, -1)
    """)


def downgrade() -> None:
    op.drop_table('plan_limits', schema='sred_ds')