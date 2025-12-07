"""Add billable_sessions table for time tracking

Revision ID: a1b2c3d4e5f6
Revises: 9b1c3d5e6f7a
Create Date: 2025-12-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9b1c3d5e6f7a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create billable_sessions table
    op.create_table(
        'billable_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=False),
        sa.Column('matter_id', UUID(as_uuid=True), nullable=True),

        # Session timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),

        # AI-generated description
        sa.Column('ai_description', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # Billing details
        sa.Column('activity_code', sa.String(50), nullable=True),
        sa.Column('is_billable', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_exported', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('exported_at', sa.DateTime(timezone=True), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        # Foreign keys with schema-qualified references
        sa.ForeignKeyConstraint(['company_id'], ['bc_legal_ds.companies.id']),
        sa.ForeignKeyConstraint(['user_id'], ['bc_legal_ds.users.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['bc_legal_ds.conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matter_id'], ['bc_legal_ds.matters.id']),

        schema='bc_legal_ds'
    )

    # Create indexes for common queries
    op.create_index(
        'ix_billable_sessions_user_id',
        'billable_sessions',
        ['user_id'],
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_billable_sessions_conversation_id',
        'billable_sessions',
        ['conversation_id'],
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_billable_sessions_matter_id',
        'billable_sessions',
        ['matter_id'],
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_billable_sessions_started_at',
        'billable_sessions',
        ['started_at'],
        schema='bc_legal_ds'
    )


def downgrade() -> None:
    op.drop_index('ix_billable_sessions_started_at', table_name='billable_sessions', schema='bc_legal_ds')
    op.drop_index('ix_billable_sessions_matter_id', table_name='billable_sessions', schema='bc_legal_ds')
    op.drop_index('ix_billable_sessions_conversation_id', table_name='billable_sessions', schema='bc_legal_ds')
    op.drop_index('ix_billable_sessions_user_id', table_name='billable_sessions', schema='bc_legal_ds')
    op.drop_table('billable_sessions', schema='bc_legal_ds')
