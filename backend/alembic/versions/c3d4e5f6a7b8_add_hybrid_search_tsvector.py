"""Add tsvector column and GIN index for hybrid search

Adds a search_vector column (tsvector) to document_chunks table for BM25/keyword search.
Creates a GIN index for fast full-text search alongside existing vector similarity search.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-12-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tsvector column for full-text search
    op.add_column(
        'document_chunks',
        sa.Column('search_vector', sa.dialects.postgresql.TSVECTOR, nullable=True),
        schema='sred_ds'
    )

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX ix_document_chunks_search_vector
        ON sred_ds.document_chunks
        USING GIN (search_vector)
    """)

    # Backfill existing chunks with tsvector data
    # Using 'english' configuration for legal documents
    op.execute("""
        UPDATE sred_ds.document_chunks
        SET search_vector = to_tsvector('english', content)
        WHERE search_vector IS NULL
    """)

    # Create trigger function to auto-update search_vector on insert/update
    op.execute("""
        CREATE OR REPLACE FUNCTION sred_ds.update_chunk_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english', NEW.content);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to automatically update search_vector
    op.execute("""
        CREATE TRIGGER trigger_update_chunk_search_vector
        BEFORE INSERT OR UPDATE OF content ON sred_ds.document_chunks
        FOR EACH ROW
        EXECUTE FUNCTION sred_ds.update_chunk_search_vector();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_update_chunk_search_vector
        ON sred_ds.document_chunks
    """)

    # Drop trigger function
    op.execute("""
        DROP FUNCTION IF EXISTS sred_ds.update_chunk_search_vector()
    """)

    # Drop GIN index
    op.execute("""
        DROP INDEX IF EXISTS sred_ds.ix_document_chunks_search_vector
    """)

    # Drop tsvector column
    op.drop_column('document_chunks', 'search_vector', schema='sred_ds')
