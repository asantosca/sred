"""Add matters and documents tables

Revision ID: de39967604e7
Revises: 
Create Date: 2025-11-04 18:15:04.973188

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'de39967604e7'
down_revision = '002_password_reset'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create matters table
    op.create_table(
        'matters',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('matter_number', sa.String(length=50), nullable=False),
        sa.Column('client_name', sa.String(length=255), nullable=False),
        sa.Column('case_type', sa.String(length=100), nullable=False),
        sa.Column('matter_status', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('opened_date', sa.Date(), nullable=False),
        sa.Column('closed_date', sa.Date(), nullable=True),
        sa.Column('lead_attorney_user_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['lead_attorney_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_matter_number', 'matters', ['matter_number'])
    op.create_index('idx_client_name', 'matters', ['client_name'])
    op.create_index('idx_matter_status', 'matters', ['matter_status'])

    # Create matter_access table
    op.create_table(
        'matter_access',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('matter_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('access_role', sa.String(length=50), nullable=False),
        sa.Column('can_upload', sa.Boolean(), nullable=True),
        sa.Column('can_edit', sa.Boolean(), nullable=True),
        sa.Column('can_delete', sa.Boolean(), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('granted_by', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['matter_id'], ['matters.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('matter_id', 'user_id')
    )
    op.create_index('idx_user_matters', 'matter_access', ['user_id'])
    op.create_index('idx_matter_users', 'matter_access', ['matter_id'])

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('matter_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_extension', sa.String(length=10), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('storage_path', sa.String(length=1000), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('document_type', sa.String(length=100), nullable=False),
        sa.Column('document_subtype', sa.String(length=100), nullable=True),
        sa.Column('document_title', sa.String(length=500), nullable=False),
        sa.Column('document_date', sa.Date(), nullable=False),
        sa.Column('date_received', sa.Date(), nullable=True),
        sa.Column('filed_date', sa.Date(), nullable=True),
        sa.Column('document_status', sa.String(length=50), nullable=False),
        sa.Column('is_current_version', sa.Boolean(), nullable=True),
        sa.Column('version_label', sa.String(length=100), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=True),
        sa.Column('parent_document_id', sa.UUID(), nullable=True),
        sa.Column('root_document_id', sa.UUID(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('superseded_date', sa.Date(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('confidentiality_level', sa.String(length=50), nullable=False),
        sa.Column('is_privileged', sa.Boolean(), nullable=True),
        sa.Column('privilege_attorney_client', sa.Boolean(), nullable=True),
        sa.Column('privilege_work_product', sa.Boolean(), nullable=True),
        sa.Column('privilege_settlement', sa.Boolean(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('recipient', sa.String(length=255), nullable=True),
        sa.Column('opposing_counsel', sa.String(length=255), nullable=True),
        sa.Column('opposing_party', sa.String(length=255), nullable=True),
        sa.Column('court_jurisdiction', sa.String(length=255), nullable=True),
        sa.Column('case_number', sa.String(length=100), nullable=True),
        sa.Column('judge_name', sa.String(length=255), nullable=True),
        sa.Column('contract_type', sa.String(length=100), nullable=True),
        sa.Column('contract_value', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('contract_effective_date', sa.Date(), nullable=True),
        sa.Column('contract_expiration_date', sa.Date(), nullable=True),
        sa.Column('governing_law', sa.String(length=100), nullable=True),
        sa.Column('discovery_type', sa.String(length=100), nullable=True),
        sa.Column('propounding_party', sa.String(length=255), nullable=True),
        sa.Column('responding_party', sa.String(length=255), nullable=True),
        sa.Column('discovery_number', sa.String(length=100), nullable=True),
        sa.Column('response_due_date', sa.Date(), nullable=True),
        sa.Column('response_status', sa.String(length=50), nullable=True),
        sa.Column('exhibit_number', sa.String(length=100), nullable=True),
        sa.Column('correspondence_type', sa.String(length=50), nullable=True),
        sa.Column('cc', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('review_status', sa.String(length=50), nullable=True),
        sa.Column('assigned_to', sa.UUID(), nullable=True),
        sa.Column('review_deadline', sa.Date(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('review_instructions', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('text_extracted', sa.Boolean(), nullable=True),
        sa.Column('indexed_for_search', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['matter_id'], ['matters.id'], ),
        sa.ForeignKeyConstraint(['parent_document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['root_document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_matter_documents', 'documents', ['matter_id', 'document_date'])
    op.create_index('idx_document_type', 'documents', ['document_type'])
    op.create_index('idx_current_versions', 'documents', ['matter_id', 'is_current_version'], postgresql_where=sa.text('is_current_version = true'))
    op.create_index('idx_version_chains', 'documents', ['root_document_id', 'version_number'])
    op.create_index('idx_file_hash', 'documents', ['file_hash'])
    op.create_index('idx_privilege', 'documents', ['is_privileged'], postgresql_where=sa.text('is_privileged = true'))
    op.create_index('idx_review_status', 'documents', ['review_status', 'assigned_to'])


def downgrade() -> None:
    op.drop_table('documents')
    op.drop_table('matter_access')
    op.drop_table('matters')