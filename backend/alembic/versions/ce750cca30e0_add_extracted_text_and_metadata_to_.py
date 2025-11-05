"""Add extracted text and metadata to documents

Revision ID: ce750cca30e0
Revises: 6b43c1e68b68
Create Date: 2025-11-05 09:19:39.839035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce750cca30e0'
down_revision = '6b43c1e68b68'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add extracted_text column to store full extracted text
    op.add_column('documents', sa.Column('extracted_text', sa.Text(), nullable=True,
                                         comment='Full text extracted from document for RAG processing'))

    # Add text extraction metadata columns
    op.add_column('documents', sa.Column('page_count', sa.Integer(), nullable=True,
                                         comment='Number of pages in document'))
    op.add_column('documents', sa.Column('word_count', sa.Integer(), nullable=True,
                                         comment='Word count of extracted text'))
    op.add_column('documents', sa.Column('extraction_method', sa.String(50), nullable=True,
                                         comment='Method used for text extraction (pdfplumber, python-docx, etc)'))
    op.add_column('documents', sa.Column('extraction_date', sa.TIMESTAMP(timezone=True), nullable=True,
                                         comment='When text extraction was completed'))
    op.add_column('documents', sa.Column('extraction_error', sa.Text(), nullable=True,
                                         comment='Error message if extraction failed'))

    # Create index on extracted_text for full-text search (using GIN for PostgreSQL)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_extracted_text_gin
        ON documents USING gin(to_tsvector('english', extracted_text))
    """)


def downgrade() -> None:
    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_documents_extracted_text_gin")

    # Drop columns
    op.drop_column('documents', 'extraction_error')
    op.drop_column('documents', 'extraction_date')
    op.drop_column('documents', 'extraction_method')
    op.drop_column('documents', 'word_count')
    op.drop_column('documents', 'page_count')
    op.drop_column('documents', 'extracted_text')