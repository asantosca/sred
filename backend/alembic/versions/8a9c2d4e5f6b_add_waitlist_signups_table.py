"""Add waitlist_signups table

Revision ID: 8a9c2d4e5f6b
Revises: fb3f0d133f87
Create Date: 2025-11-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '8a9c2d4e5f6b'
down_revision = 'fb3f0d133f87'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create waitlist_signups table
    op.create_table(
        'waitlist_signups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),  # 'landing_page', 'contact_page', etc.
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('converted_to_user', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        schema='bc_legal_ds'
    )

    # Create index on email for faster lookups
    op.create_index(
        'ix_waitlist_signups_email',
        'waitlist_signups',
        ['email'],
        schema='bc_legal_ds'
    )

    # Create index on created_at for sorting
    op.create_index(
        'ix_waitlist_signups_created_at',
        'waitlist_signups',
        ['created_at'],
        schema='bc_legal_ds'
    )

    # Add foreign key to users table (for conversion tracking)
    op.create_foreign_key(
        'fk_waitlist_signups_user_id',
        'waitlist_signups', 'users',
        ['user_id'], ['id'],
        source_schema='bc_legal_ds',
        referent_schema='bc_legal_ds',
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_waitlist_signups_created_at', table_name='waitlist_signups', schema='bc_legal_ds')
    op.drop_index('ix_waitlist_signups_email', table_name='waitlist_signups', schema='bc_legal_ds')

    # Drop table
    op.drop_table('waitlist_signups', schema='bc_legal_ds')
