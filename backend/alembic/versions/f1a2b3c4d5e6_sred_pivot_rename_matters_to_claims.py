"""sred_pivot_rename_matters_to_claims

Revision ID: f1a2b3c4d5e6
Revises: 719388e67d8c
Create Date: 2025-01-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '719388e67d8c'
branch_labels = None
depends_on = None

SCHEMA = 'bc_legal_ds'


def upgrade() -> None:
    # ==========================================================================
    # SR&ED PIVOT MIGRATION
    # Renames matters -> claims and updates terminology for SR&ED platform
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Step 1: Drop foreign key constraints that reference matters
    # --------------------------------------------------------------------------

    # Drop FK from matter_access
    op.drop_constraint('matter_access_matter_id_fkey', 'matter_access', schema=SCHEMA, type_='foreignkey')

    # Drop FK from documents
    op.drop_constraint('documents_matter_id_fkey', 'documents', schema=SCHEMA, type_='foreignkey')

    # Drop FK from conversations
    op.drop_constraint('conversations_matter_id_fkey', 'conversations', schema=SCHEMA, type_='foreignkey')

    # Drop FK from billable_sessions
    op.drop_constraint('billable_sessions_matter_id_fkey', 'billable_sessions', schema=SCHEMA, type_='foreignkey')

    # Drop FK from document_events
    op.drop_constraint('document_events_matter_id_fkey', 'document_events', schema=SCHEMA, type_='foreignkey')

    # --------------------------------------------------------------------------
    # Step 2: Rename matters table to claims
    # --------------------------------------------------------------------------
    op.rename_table('matters', 'claims', schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 3: Rename matter_access table to claim_access
    # --------------------------------------------------------------------------
    op.rename_table('matter_access', 'claim_access', schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 4: Rename columns in claims table
    # --------------------------------------------------------------------------

    # matter_number -> claim_number
    op.alter_column('claims', 'matter_number', new_column_name='claim_number', schema=SCHEMA)

    # client_name -> company_name
    op.alter_column('claims', 'client_name', new_column_name='company_name', schema=SCHEMA)

    # matter_type -> project_type
    op.alter_column('claims', 'matter_type', new_column_name='project_type', schema=SCHEMA)

    # matter_status -> claim_status
    op.alter_column('claims', 'matter_status', new_column_name='claim_status', schema=SCHEMA)

    # lead_attorney_user_id -> lead_consultant_user_id
    op.alter_column('claims', 'lead_attorney_user_id', new_column_name='lead_consultant_user_id', schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 5: Add new SR&ED-specific columns to claims
    # --------------------------------------------------------------------------

    # Fiscal year end date (required for SR&ED claims)
    op.add_column('claims', sa.Column('fiscal_year_end', sa.Date(), nullable=True), schema=SCHEMA)

    # NAICS industry classification code
    op.add_column('claims', sa.Column('naics_code', sa.String(10), nullable=True), schema=SCHEMA)

    # CRA business number
    op.add_column('claims', sa.Column('cra_business_number', sa.String(15), nullable=True), schema=SCHEMA)

    # Expenditure tracking
    op.add_column('claims', sa.Column('total_eligible_expenditures', sa.DECIMAL(15, 2), nullable=True), schema=SCHEMA)
    op.add_column('claims', sa.Column('federal_credit_estimate', sa.DECIMAL(15, 2), nullable=True), schema=SCHEMA)
    op.add_column('claims', sa.Column('provincial_credit_estimate', sa.DECIMAL(15, 2), nullable=True), schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 6: Rename matter_id columns in related tables to claim_id
    # --------------------------------------------------------------------------

    # claim_access: matter_id -> claim_id
    op.alter_column('claim_access', 'matter_id', new_column_name='claim_id', schema=SCHEMA)

    # documents: matter_id -> claim_id
    op.alter_column('documents', 'matter_id', new_column_name='claim_id', schema=SCHEMA)

    # conversations: matter_id -> claim_id
    op.alter_column('conversations', 'matter_id', new_column_name='claim_id', schema=SCHEMA)

    # billable_sessions: matter_id -> claim_id
    op.alter_column('billable_sessions', 'matter_id', new_column_name='claim_id', schema=SCHEMA)

    # document_events: matter_id -> claim_id
    op.alter_column('document_events', 'matter_id', new_column_name='claim_id', schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 7: Recreate foreign key constraints pointing to claims
    # --------------------------------------------------------------------------

    # claim_access -> claims
    op.create_foreign_key(
        'claim_access_claim_id_fkey',
        'claim_access', 'claims',
        ['claim_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )

    # documents -> claims
    op.create_foreign_key(
        'documents_claim_id_fkey',
        'documents', 'claims',
        ['claim_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )

    # conversations -> claims
    op.create_foreign_key(
        'conversations_claim_id_fkey',
        'conversations', 'claims',
        ['claim_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )

    # billable_sessions -> claims
    op.create_foreign_key(
        'billable_sessions_claim_id_fkey',
        'billable_sessions', 'claims',
        ['claim_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )

    # document_events -> claims
    op.create_foreign_key(
        'document_events_claim_id_fkey',
        'document_events', 'claims',
        ['claim_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )


def downgrade() -> None:
    # ==========================================================================
    # REVERSE: Rename claims back to matters
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Step 1: Drop foreign key constraints
    # --------------------------------------------------------------------------
    op.drop_constraint('claim_access_claim_id_fkey', 'claim_access', schema=SCHEMA, type_='foreignkey')
    op.drop_constraint('documents_claim_id_fkey', 'documents', schema=SCHEMA, type_='foreignkey')
    op.drop_constraint('conversations_claim_id_fkey', 'conversations', schema=SCHEMA, type_='foreignkey')
    op.drop_constraint('billable_sessions_claim_id_fkey', 'billable_sessions', schema=SCHEMA, type_='foreignkey')
    op.drop_constraint('document_events_claim_id_fkey', 'document_events', schema=SCHEMA, type_='foreignkey')

    # --------------------------------------------------------------------------
    # Step 2: Rename claim_id columns back to matter_id
    # --------------------------------------------------------------------------
    op.alter_column('claim_access', 'claim_id', new_column_name='matter_id', schema=SCHEMA)
    op.alter_column('documents', 'claim_id', new_column_name='matter_id', schema=SCHEMA)
    op.alter_column('conversations', 'claim_id', new_column_name='matter_id', schema=SCHEMA)
    op.alter_column('billable_sessions', 'claim_id', new_column_name='matter_id', schema=SCHEMA)
    op.alter_column('document_events', 'claim_id', new_column_name='matter_id', schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 3: Drop SR&ED-specific columns
    # --------------------------------------------------------------------------
    op.drop_column('claims', 'provincial_credit_estimate', schema=SCHEMA)
    op.drop_column('claims', 'federal_credit_estimate', schema=SCHEMA)
    op.drop_column('claims', 'total_eligible_expenditures', schema=SCHEMA)
    op.drop_column('claims', 'cra_business_number', schema=SCHEMA)
    op.drop_column('claims', 'naics_code', schema=SCHEMA)
    op.drop_column('claims', 'fiscal_year_end', schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 4: Rename columns back in claims table
    # --------------------------------------------------------------------------
    op.alter_column('claims', 'claim_number', new_column_name='matter_number', schema=SCHEMA)
    op.alter_column('claims', 'company_name', new_column_name='client_name', schema=SCHEMA)
    op.alter_column('claims', 'project_type', new_column_name='matter_type', schema=SCHEMA)
    op.alter_column('claims', 'claim_status', new_column_name='matter_status', schema=SCHEMA)
    op.alter_column('claims', 'lead_consultant_user_id', new_column_name='lead_attorney_user_id', schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 5: Rename tables back
    # --------------------------------------------------------------------------
    op.rename_table('claim_access', 'matter_access', schema=SCHEMA)
    op.rename_table('claims', 'matters', schema=SCHEMA)

    # --------------------------------------------------------------------------
    # Step 6: Recreate original foreign key constraints
    # --------------------------------------------------------------------------
    op.create_foreign_key(
        'matter_access_matter_id_fkey',
        'matter_access', 'matters',
        ['matter_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )
    op.create_foreign_key(
        'documents_matter_id_fkey',
        'documents', 'matters',
        ['matter_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )
    op.create_foreign_key(
        'conversations_matter_id_fkey',
        'conversations', 'matters',
        ['matter_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )
    op.create_foreign_key(
        'billable_sessions_matter_id_fkey',
        'billable_sessions', 'matters',
        ['matter_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )
    op.create_foreign_key(
        'document_events_matter_id_fkey',
        'document_events', 'matters',
        ['matter_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )
