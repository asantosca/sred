"""increase_document_size_limits_for_sred

Revision ID: 89a9a5b9c924
Revises: f1a2b3c4d5e6
Create Date: 2026-01-15 20:03:23.105920

SR&ED documents are typically larger than standard legal documents.
Increasing max_document_size_mb limits to accommodate:
- Technical reports with diagrams
- Scanned lab notebooks
- Large project documentation compilations

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89a9a5b9c924'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update document size limits for all tiers to accommodate large SR&ED documents
    # SR&ED documents (technical reports, scanned lab notebooks) are often 200-500MB
    # Previous limits: free=10MB, basic=50MB, professional=100MB, enterprise=500MB
    # New limits: All tiers get 500MB for document size (storage limits still apply per tier)
    op.execute("""
        UPDATE bc_legal_ds.plan_limits
        SET max_document_size_mb = 500
    """)


def downgrade() -> None:
    # Restore original document size limits
    op.execute("""
        UPDATE bc_legal_ds.plan_limits
        SET max_document_size_mb = CASE plan_tier
            WHEN 'free' THEN 10
            WHEN 'basic' THEN 50
            WHEN 'professional' THEN 100
            WHEN 'enterprise' THEN 500
            ELSE max_document_size_mb
        END
    """)