"""Add workspace fields to conversations for project discovery workspace

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-01-19 10:00:00.000000

Adds fields to conversations for the collaborative project workspace:
- conversation_type: Distinguishes general chat from project_workspace
- workspace_md: Markdown content for discovered projects
- last_discovery_at: Timestamp of last discovery run
- known_document_ids: JSON array for change detection

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'c4d5e6f7a8b9'
down_revision = 'b3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add workspace fields to conversations
    op.add_column(
        'conversations',
        sa.Column('conversation_type', sa.String(50), server_default='general', nullable=True),
        schema='sred_ds'
    )
    op.add_column(
        'conversations',
        sa.Column('workspace_md', sa.Text(), nullable=True),
        schema='sred_ds'
    )
    op.add_column(
        'conversations',
        sa.Column('last_discovery_at', sa.DateTime(timezone=True), nullable=True),
        schema='sred_ds'
    )
    op.add_column(
        'conversations',
        sa.Column('known_document_ids', JSON(), nullable=True),
        schema='sred_ds'
    )

    # Create partial unique index: only one project_workspace per claim
    op.execute("""
        CREATE UNIQUE INDEX uq_conversations_claim_workspace
        ON sred_ds.conversations (claim_id)
        WHERE conversation_type = 'project_workspace'
    """)

    # Index for filtering by conversation_type
    op.create_index(
        'ix_conversations_type',
        'conversations',
        ['conversation_type'],
        schema='sred_ds'
    )


def downgrade() -> None:
    op.drop_index('ix_conversations_type', table_name='conversations', schema='sred_ds')
    op.execute("DROP INDEX IF EXISTS sred_ds.uq_conversations_claim_workspace")
    op.drop_column('conversations', 'known_document_ids', schema='sred_ds')
    op.drop_column('conversations', 'last_discovery_at', schema='sred_ds')
    op.drop_column('conversations', 'workspace_md', schema='sred_ds')
    op.drop_column('conversations', 'conversation_type', schema='sred_ds')
