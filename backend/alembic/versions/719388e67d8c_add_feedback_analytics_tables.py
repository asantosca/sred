"""add_feedback_analytics_tables

Revision ID: 719388e67d8c
Revises: 7af4d1da845f
Create Date: 2025-12-20 11:00:57.236138

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = '719388e67d8c'
down_revision = '7af4d1da845f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add feedback_category to messages table
    op.add_column(
        'messages',
        sa.Column('feedback_category', sa.String(50), nullable=True),
        schema='bc_legal_ds'
    )

    # 2. Create message_feedback_details table
    op.create_table(
        'message_feedback_details',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('message_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.messages.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.companies.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.users.id'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback_category', sa.String(50), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_message_feedback_details_company_id',
        'message_feedback_details',
        ['company_id'],
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_message_feedback_details_rating',
        'message_feedback_details',
        ['rating'],
        schema='bc_legal_ds'
    )

    # 3. Create conversation_signals table
    op.create_table(
        'conversation_signals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.companies.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.users.id'), nullable=False),
        sa.Column('session_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('session_ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rephrase_count', sa.Integer(), server_default='0'),
        sa.Column('copy_events', sa.Integer(), server_default='0'),
        sa.Column('source_clicks', sa.Integer(), server_default='0'),
        sa.Column('is_abandoned', sa.Boolean(), server_default='false'),
        sa.Column('conversation_continued', sa.Boolean(), server_default='false'),
        sa.Column('billable_created', sa.Boolean(), server_default='false'),
        sa.Column('last_user_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_ai_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_conversation_signals_conversation_id',
        'conversation_signals',
        ['conversation_id'],
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_conversation_signals_company_id',
        'conversation_signals',
        ['company_id'],
        schema='bc_legal_ds'
    )

    # 4. Create message_quality_scores table
    op.create_table(
        'message_quality_scores',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('message_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.messages.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.companies.id'), nullable=False),
        sa.Column('query_length', sa.Integer(), nullable=True),
        sa.Column('query_word_count', sa.Integer(), nullable=True),
        sa.Column('has_matter_context', sa.Boolean(), server_default='false'),
        sa.Column('has_document_context', sa.Boolean(), server_default='false'),
        sa.Column('is_follow_up_to_rephrase', sa.Boolean(), server_default='false'),
        sa.Column('question_quality_score', sa.Float(), nullable=True),
        sa.Column('explicit_feedback_score', sa.Float(), nullable=True),
        sa.Column('implicit_signal_score', sa.Float(), nullable=True),
        sa.Column('context_relevance_score', sa.Float(), nullable=True),
        sa.Column('overall_confidence_score', sa.Float(), nullable=True),
        sa.Column('scored_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('score_version', sa.String(10), server_default="'1.0'"),
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_message_quality_scores_company_id',
        'message_quality_scores',
        ['company_id'],
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_message_quality_scores_confidence',
        'message_quality_scores',
        ['overall_confidence_score'],
        schema='bc_legal_ds'
    )

    # 5. Create feedback_aggregates table
    op.create_table(
        'feedback_aggregates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.companies.id'), nullable=True),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_messages', sa.Integer(), server_default='0'),
        sa.Column('total_feedback', sa.Integer(), server_default='0'),
        sa.Column('positive_count', sa.Integer(), server_default='0'),
        sa.Column('negative_count', sa.Integer(), server_default='0'),
        sa.Column('positive_rate', sa.Float(), nullable=True),
        sa.Column('rephrase_rate', sa.Float(), nullable=True),
        sa.Column('abandonment_rate', sa.Float(), nullable=True),
        sa.Column('engagement_rate', sa.Float(), nullable=True),
        sa.Column('feedback_by_category', JSON(), nullable=True),
        sa.Column('avg_question_quality', sa.Float(), nullable=True),
        sa.Column('avg_response_confidence', sa.Float(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_feedback_aggregates_period',
        'feedback_aggregates',
        ['period_type', 'period_start'],
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_feedback_aggregates_company_id',
        'feedback_aggregates',
        ['company_id'],
        schema='bc_legal_ds'
    )

    # 6. Create feedback_alerts table
    op.create_table(
        'feedback_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('bc_legal_ds.companies.id'), nullable=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('time_window_minutes', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('alert_details', JSON(), nullable=True),
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_feedback_alerts_active',
        'feedback_alerts',
        ['is_active'],
        schema='bc_legal_ds'
    )
    op.create_index(
        'ix_feedback_alerts_company_id',
        'feedback_alerts',
        ['company_id'],
        schema='bc_legal_ds'
    )


def downgrade() -> None:
    # Drop indexes and tables in reverse order
    op.drop_index('ix_feedback_alerts_company_id', table_name='feedback_alerts', schema='bc_legal_ds')
    op.drop_index('ix_feedback_alerts_active', table_name='feedback_alerts', schema='bc_legal_ds')
    op.drop_table('feedback_alerts', schema='bc_legal_ds')

    op.drop_index('ix_feedback_aggregates_company_id', table_name='feedback_aggregates', schema='bc_legal_ds')
    op.drop_index('ix_feedback_aggregates_period', table_name='feedback_aggregates', schema='bc_legal_ds')
    op.drop_table('feedback_aggregates', schema='bc_legal_ds')

    op.drop_index('ix_message_quality_scores_confidence', table_name='message_quality_scores', schema='bc_legal_ds')
    op.drop_index('ix_message_quality_scores_company_id', table_name='message_quality_scores', schema='bc_legal_ds')
    op.drop_table('message_quality_scores', schema='bc_legal_ds')

    op.drop_index('ix_conversation_signals_company_id', table_name='conversation_signals', schema='bc_legal_ds')
    op.drop_index('ix_conversation_signals_conversation_id', table_name='conversation_signals', schema='bc_legal_ds')
    op.drop_table('conversation_signals', schema='bc_legal_ds')

    op.drop_index('ix_message_feedback_details_rating', table_name='message_feedback_details', schema='bc_legal_ds')
    op.drop_index('ix_message_feedback_details_company_id', table_name='message_feedback_details', schema='bc_legal_ds')
    op.drop_table('message_feedback_details', schema='bc_legal_ds')

    op.drop_column('messages', 'feedback_category', schema='bc_legal_ds')
