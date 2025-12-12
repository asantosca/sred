"""add OCR tracking fields to documents

Revision ID: e5f6a7b8c9d0
Revises: 2a8b383d4a6b
Create Date: 2025-12-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = '2a8b383d4a6b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add OCR tracking fields to documents table
    op.add_column('documents', sa.Column('ocr_applied', sa.Boolean(), nullable=False, server_default='false'), schema='bc_legal_ds')
    op.add_column('documents', sa.Column('ocr_engine', sa.String(50), nullable=True), schema='bc_legal_ds')
    op.add_column('documents', sa.Column('ocr_pages_processed', sa.Integer(), nullable=True), schema='bc_legal_ds')
    op.add_column('documents', sa.Column('ocr_confidence_avg', sa.Float(), nullable=True), schema='bc_legal_ds')


def downgrade() -> None:
    op.drop_column('documents', 'ocr_confidence_avg', schema='bc_legal_ds')
    op.drop_column('documents', 'ocr_pages_processed', schema='bc_legal_ds')
    op.drop_column('documents', 'ocr_engine', schema='bc_legal_ds')
    op.drop_column('documents', 'ocr_applied', schema='bc_legal_ds')
