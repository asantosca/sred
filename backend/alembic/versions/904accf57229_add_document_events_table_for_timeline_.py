"""Add document_events table for timeline feature

Revision ID: 904accf57229
Revises: d4e5f6a7b8c9
Create Date: 2025-12-08 15:47:52.587096

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '904accf57229'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None

SCHEMA = 'sred_ds'


def upgrade() -> None:
    op.create_table(
        'document_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.companies.id'), nullable=False),
        sa.Column('matter_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.matters.id'), nullable=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.document_chunks.id', ondelete='SET NULL'), nullable=True),

        # Event data
        sa.Column('event_date', sa.Date, nullable=False),
        sa.Column('event_description', sa.Text, nullable=False),

        # Date precision and confidence
        sa.Column('date_precision', sa.String(10), nullable=False, server_default='day'),  # day, month, year, unknown
        sa.Column('confidence', sa.String(10), nullable=False, server_default='high'),  # high, medium, low
        sa.Column('raw_date_text', sa.String(255), nullable=True),  # original text from document

        # User overrides
        sa.Column('is_user_created', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_user_modified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('user_notes', sa.Text, nullable=True),

        # Versioning - track which document version this came from
        sa.Column('document_version', sa.Integer, nullable=True),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),  # when newer version replaced this

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.users.id'), nullable=True),  # null for AI-extracted

        schema=SCHEMA
    )

    # Indexes for common query patterns
    op.create_index(
        'ix_document_events_company_id',
        'document_events',
        ['company_id'],
        schema=SCHEMA
    )
    op.create_index(
        'ix_document_events_matter_id',
        'document_events',
        ['matter_id'],
        schema=SCHEMA
    )
    op.create_index(
        'ix_document_events_document_id',
        'document_events',
        ['document_id'],
        schema=SCHEMA
    )
    op.create_index(
        'ix_document_events_event_date',
        'document_events',
        ['event_date'],
        schema=SCHEMA
    )
    # Composite index for timeline queries (company + date range)
    op.create_index(
        'ix_document_events_company_date',
        'document_events',
        ['company_id', 'event_date'],
        schema=SCHEMA
    )
    # Index for filtering active (non-superseded) events
    op.create_index(
        'ix_document_events_active',
        'document_events',
        ['company_id', 'superseded_at'],
        schema=SCHEMA,
        postgresql_where=sa.text('superseded_at IS NULL')
    )


def downgrade() -> None:
    op.drop_index('ix_document_events_active', table_name='document_events', schema=SCHEMA)
    op.drop_index('ix_document_events_company_date', table_name='document_events', schema=SCHEMA)
    op.drop_index('ix_document_events_event_date', table_name='document_events', schema=SCHEMA)
    op.drop_index('ix_document_events_document_id', table_name='document_events', schema=SCHEMA)
    op.drop_index('ix_document_events_matter_id', table_name='document_events', schema=SCHEMA)
    op.drop_index('ix_document_events_company_id', table_name='document_events', schema=SCHEMA)
    op.drop_table('document_events', schema=SCHEMA)
