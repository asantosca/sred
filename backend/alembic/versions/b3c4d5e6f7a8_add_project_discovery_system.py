"""add_project_discovery_system

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-01-18 10:00:00.000000

Add tables and columns for SR&ED project discovery system:
- projects: R&D project records with SR&ED scores and T661 narratives
- document_project_tags: Many-to-many document-to-project mapping
- project_discovery_runs: Discovery execution history
- document_upload_batches: Change detection for incremental uploads
- Extend documents with sred_signals, temporal_metadata
- Extend document_chunks with sred_keyword_matches

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY


# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create document_upload_batches table (needed for FK in documents)
    op.create_table(
        'document_upload_batches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('claim_id', UUID(as_uuid=True), sa.ForeignKey('sred_ds.claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_number', sa.Integer(), nullable=True),
        sa.Column('document_count', sa.Integer(), nullable=True),
        sa.Column('total_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('analyzed', sa.Boolean(), server_default='false'),
        sa.Column('analysis_run_id', UUID(as_uuid=True), nullable=True),  # FK added after project_discovery_runs
        sa.Column('impact_summary', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('sred_ds.users.id'), nullable=True),
        schema='sred_ds'
    )
    op.create_index(
        'ix_document_upload_batches_claim_id',
        'document_upload_batches',
        ['claim_id'],
        schema='sred_ds'
    )
    op.create_index(
        'ix_document_upload_batches_analyzed',
        'document_upload_batches',
        ['analyzed'],
        schema='sred_ds'
    )

    # 2. Create projects table
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('claim_id', UUID(as_uuid=True), sa.ForeignKey('sred_ds.claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('sred_ds.companies.id', ondelete='CASCADE'), nullable=False),

        # Project Identity
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('project_code', sa.String(50), nullable=True),

        # SR&ED Classification
        sa.Column('sred_confidence_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('project_status', sa.String(50), server_default="'discovered'"),

        # Discovery Metadata
        sa.Column('discovery_method', sa.String(50), nullable=True),
        sa.Column('ai_suggested', sa.Boolean(), server_default='false'),
        sa.Column('user_confirmed', sa.Boolean(), server_default='false'),

        # Temporal Info
        sa.Column('project_start_date', sa.Date(), nullable=True),
        sa.Column('project_end_date', sa.Date(), nullable=True),

        # Team Info
        sa.Column('team_members', ARRAY(sa.String), nullable=True),
        sa.Column('team_size', sa.Integer(), nullable=True),

        # Financial
        sa.Column('estimated_spend', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('eligible_expenditures', sa.DECIMAL(15, 2), nullable=True),

        # SR&ED Signals (aggregated from documents)
        sa.Column('uncertainty_signal_count', sa.Integer(), server_default='0'),
        sa.Column('systematic_signal_count', sa.Integer(), server_default='0'),
        sa.Column('failure_signal_count', sa.Integer(), server_default='0'),
        sa.Column('advancement_signal_count', sa.Integer(), server_default='0'),

        # AI-Generated Summaries
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('uncertainty_summary', sa.Text(), nullable=True),
        sa.Column('work_summary', sa.Text(), nullable=True),
        sa.Column('advancement_summary', sa.Text(), nullable=True),

        # Narrative Status
        sa.Column('narrative_status', sa.String(50), server_default="'not_started'"),
        sa.Column('narrative_line_242', sa.Text(), nullable=True),
        sa.Column('narrative_line_244', sa.Text(), nullable=True),
        sa.Column('narrative_line_246', sa.Text(), nullable=True),
        sa.Column('narrative_word_count_242', sa.Integer(), nullable=True),
        sa.Column('narrative_word_count_244', sa.Integer(), nullable=True),
        sa.Column('narrative_word_count_246', sa.Integer(), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('sred_ds.users.id'), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('sred_ds.users.id'), nullable=True),
        schema='sred_ds'
    )
    op.create_index('ix_projects_claim_id', 'projects', ['claim_id'], schema='sred_ds')
    op.create_index('ix_projects_company_id', 'projects', ['company_id'], schema='sred_ds')
    op.create_index('ix_projects_status', 'projects', ['project_status'], schema='sred_ds')
    op.create_index('ix_projects_confidence', 'projects', ['sred_confidence_score'], schema='sred_ds')

    # 3. Create document_project_tags table (many-to-many)
    op.create_table(
        'document_project_tags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('sred_ds.documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('sred_ds.projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tagged_by', sa.String(50), nullable=False),  # 'ai' or 'user'
        sa.Column('confidence_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('page_ranges', sa.Text(), nullable=True),  # JSON string
        sa.Column('relevance_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('sred_ds.users.id'), nullable=True),
        sa.UniqueConstraint('document_id', 'project_id', name='uq_document_project_tags_doc_proj'),
        schema='sred_ds'
    )
    op.create_index('ix_document_project_tags_document_id', 'document_project_tags', ['document_id'], schema='sred_ds')
    op.create_index('ix_document_project_tags_project_id', 'document_project_tags', ['project_id'], schema='sred_ds')
    op.create_index('ix_document_project_tags_confidence', 'document_project_tags', ['confidence_score'], schema='sred_ds')

    # 4. Create project_discovery_runs table
    op.create_table(
        'project_discovery_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('claim_id', UUID(as_uuid=True), sa.ForeignKey('sred_ds.claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_documents_analyzed', sa.Integer(), nullable=True),
        sa.Column('discovery_algorithm', sa.String(50), nullable=True),
        sa.Column('parameters', JSON(), nullable=True),
        sa.Column('projects_discovered', sa.Integer(), nullable=True),
        sa.Column('high_confidence_count', sa.Integer(), nullable=True),
        sa.Column('medium_confidence_count', sa.Integer(), nullable=True),
        sa.Column('low_confidence_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_seconds', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),  # 'running', 'completed', 'failed'
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('sred_ds.users.id'), nullable=True),
        schema='sred_ds'
    )
    op.create_index('ix_project_discovery_runs_claim_id', 'project_discovery_runs', ['claim_id'], schema='sred_ds')
    op.create_index('ix_project_discovery_runs_created_at', 'project_discovery_runs', ['created_at'], schema='sred_ds')

    # 5. Add FK from document_upload_batches to project_discovery_runs
    op.create_foreign_key(
        'fk_document_upload_batches_analysis_run',
        'document_upload_batches',
        'project_discovery_runs',
        ['analysis_run_id'],
        ['id'],
        source_schema='sred_ds',
        referent_schema='sred_ds'
    )

    # 6. Extend documents table with SR&ED signal columns
    op.add_column('documents', sa.Column('sred_signals', JSON(), nullable=True), schema='sred_ds')
    op.add_column('documents', sa.Column('temporal_metadata', JSON(), nullable=True), schema='sred_ds')
    op.add_column('documents', sa.Column('upload_batch_id', UUID(as_uuid=True), nullable=True), schema='sred_ds')

    op.create_foreign_key(
        'fk_documents_upload_batch',
        'documents',
        'document_upload_batches',
        ['upload_batch_id'],
        ['id'],
        source_schema='sred_ds',
        referent_schema='sred_ds'
    )

    # 7. Extend document_chunks table with SR&ED keyword matches
    op.add_column('document_chunks', sa.Column('sred_keyword_matches', JSON(), nullable=True), schema='sred_ds')


def downgrade() -> None:
    # Remove columns from document_chunks
    op.drop_column('document_chunks', 'sred_keyword_matches', schema='sred_ds')

    # Remove FK and columns from documents
    op.drop_constraint('fk_documents_upload_batch', 'documents', schema='sred_ds', type_='foreignkey')
    op.drop_column('documents', 'upload_batch_id', schema='sred_ds')
    op.drop_column('documents', 'temporal_metadata', schema='sred_ds')
    op.drop_column('documents', 'sred_signals', schema='sred_ds')

    # Drop FK from document_upload_batches
    op.drop_constraint('fk_document_upload_batches_analysis_run', 'document_upload_batches', schema='sred_ds', type_='foreignkey')

    # Drop project_discovery_runs
    op.drop_index('ix_project_discovery_runs_created_at', table_name='project_discovery_runs', schema='sred_ds')
    op.drop_index('ix_project_discovery_runs_claim_id', table_name='project_discovery_runs', schema='sred_ds')
    op.drop_table('project_discovery_runs', schema='sred_ds')

    # Drop document_project_tags
    op.drop_index('ix_document_project_tags_confidence', table_name='document_project_tags', schema='sred_ds')
    op.drop_index('ix_document_project_tags_project_id', table_name='document_project_tags', schema='sred_ds')
    op.drop_index('ix_document_project_tags_document_id', table_name='document_project_tags', schema='sred_ds')
    op.drop_table('document_project_tags', schema='sred_ds')

    # Drop projects
    op.drop_index('ix_projects_confidence', table_name='projects', schema='sred_ds')
    op.drop_index('ix_projects_status', table_name='projects', schema='sred_ds')
    op.drop_index('ix_projects_company_id', table_name='projects', schema='sred_ds')
    op.drop_index('ix_projects_claim_id', table_name='projects', schema='sred_ds')
    op.drop_table('projects', schema='sred_ds')

    # Drop document_upload_batches
    op.drop_index('ix_document_upload_batches_analyzed', table_name='document_upload_batches', schema='sred_ds')
    op.drop_index('ix_document_upload_batches_claim_id', table_name='document_upload_batches', schema='sred_ds')
    op.drop_table('document_upload_batches', schema='sred_ds')
