"""Add RAG pipeline tables (chunks, relationships, processing queue)

Revision ID: 7fd19330d81e
Revises: de39967604e7
Create Date: 2025-11-04 23:26:07.462482

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '7fd19330d81e'
down_revision = 'de39967604e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create document_chunks table for RAG
    op.create_table(
        'document_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, comment='Order of chunk in document'),
        sa.Column('content', sa.Text(), nullable=False, comment='Chunk text content'),
        sa.Column('embedding', Vector(1536), nullable=True, comment='Vector embedding (default: OpenAI 1536 dims)'),
        sa.Column('embedding_model', sa.String(100), nullable=True, comment='Model used for embedding'),
        sa.Column('metadata', JSONB, nullable=True, comment='Page number, section, headers, etc.'),
        sa.Column('token_count', sa.Integer(), nullable=True, comment='Approximate token count'),
        sa.Column('char_count', sa.Integer(), nullable=False, comment='Character count'),
        sa.Column('start_char', sa.Integer(), nullable=True, comment='Start position in original document'),
        sa.Column('end_char', sa.Integer(), nullable=True, comment='End position in original document'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk_index')
    )

    # Create indexes for efficient retrieval
    op.create_index('idx_chunks_document', 'document_chunks', ['document_id'])
    op.create_index('idx_chunks_embedding', 'document_chunks', ['embedding'], postgresql_using='ivfflat', postgresql_with={'lists': 100})

    # Create document_relationships table
    op.create_table(
        'document_relationships',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('target_document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False, comment='amendment, exhibit, response, supersedes, attachment'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['source_document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('source_document_id', 'target_document_id', 'relationship_type',
                           name='uq_document_relationship')
    )

    # Create indexes
    op.create_index('idx_relationships_source', 'document_relationships', ['source_document_id'])
    op.create_index('idx_relationships_target', 'document_relationships', ['target_document_id'])
    op.create_index('idx_relationships_type', 'document_relationships', ['relationship_type'])

    # Create document_processing_queue table
    op.create_table(
        'document_processing_queue',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False, comment='extract_text, generate_embeddings, ocr, analyze'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='pending, processing, completed, failed'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5', comment='1-10, lower = higher priority'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result_data', JSONB, nullable=True, comment='Processing results or metadata'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('worker_id', sa.String(100), nullable=True, comment='ID of worker processing the task'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )

    # Create indexes for queue processing
    op.create_index('idx_queue_status_priority', 'document_processing_queue', ['status', 'priority', 'created_at'])
    op.create_index('idx_queue_document', 'document_processing_queue', ['document_id'])
    op.create_index('idx_queue_task_type', 'document_processing_queue', ['task_type', 'status'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('document_processing_queue')
    op.drop_table('document_relationships')
    op.drop_table('document_chunks')