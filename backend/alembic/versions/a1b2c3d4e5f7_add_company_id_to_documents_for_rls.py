"""Add company_id to documents for RLS performance

Revision ID: a1b2c3d4e5f7
Revises: 719388e67d8c
Create Date: 2024-12-24

This migration adds a denormalized company_id column to the documents table
to improve Row Level Security (RLS) query performance. Previously, RLS policies
had to join documents -> matters -> companies which is slower on large datasets.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = '719388e67d8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add company_id column (nullable first to allow backfill)
    op.add_column(
        'documents',
        sa.Column('company_id', sa.UUID(), nullable=True),
        schema='bc_legal_ds'
    )

    # Backfill company_id from matters table
    op.execute("""
        UPDATE bc_legal_ds.documents d
        SET company_id = m.company_id
        FROM bc_legal_ds.matters m
        WHERE d.matter_id = m.id
    """)

    # Make column non-nullable after backfill
    op.alter_column(
        'documents',
        'company_id',
        nullable=False,
        schema='bc_legal_ds'
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_documents_company_id',
        'documents',
        'companies',
        ['company_id'],
        ['id'],
        source_schema='bc_legal_ds',
        referent_schema='bc_legal_ds'
    )

    # Add index for RLS performance
    op.create_index(
        'idx_documents_company_id',
        'documents',
        ['company_id'],
        schema='bc_legal_ds'
    )


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_documents_company_id', table_name='documents', schema='bc_legal_ds')

    # Remove foreign key
    op.drop_constraint('fk_documents_company_id', 'documents', schema='bc_legal_ds', type_='foreignkey')

    # Remove column
    op.drop_column('documents', 'company_id', schema='bc_legal_ds')
