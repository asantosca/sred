"""Add daily briefings table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2024-12-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'daily_briefings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('briefing_date', sa.Date(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('context_summary', postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['bc_legal_ds.companies.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['bc_legal_ds.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='bc_legal_ds'
    )

    # Index for quick lookup by user and date
    op.create_index(
        'ix_daily_briefings_user_date',
        'daily_briefings',
        ['user_id', 'briefing_date'],
        unique=True,
        schema='bc_legal_ds'
    )


def downgrade() -> None:
    op.drop_index('ix_daily_briefings_user_date', table_name='daily_briefings', schema='bc_legal_ds')
    op.drop_table('daily_briefings', schema='bc_legal_ds')
