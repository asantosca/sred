"""Add summary field to conversations for searchable chat history

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add summary fields to conversations
    op.add_column(
        'conversations',
        sa.Column('summary', sa.Text(), nullable=True),
        schema='bc_legal_ds'
    )
    op.add_column(
        'conversations',
        sa.Column('summary_generated_at', sa.DateTime(timezone=True), nullable=True),
        schema='bc_legal_ds'
    )

    # Create GIN index for full-text search on summary
    op.execute("""
        CREATE INDEX ix_conversations_summary_search
        ON bc_legal_ds.conversations
        USING GIN (to_tsvector('english', COALESCE(summary, '') || ' ' || COALESCE(title, '')))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS bc_legal_ds.ix_conversations_summary_search")
    op.drop_column('conversations', 'summary_generated_at', schema='bc_legal_ds')
    op.drop_column('conversations', 'summary', schema='bc_legal_ds')
