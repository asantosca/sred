"""Add CASL consent tracking to waitlist_signups

Revision ID: 9b1c3d5e6f7a
Revises: 8a9c2d4e5f6b
Create Date: 2025-11-09 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b1c3d5e6f7a'
down_revision = '8a9c2d4e5f6b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add CASL consent tracking fields
    op.add_column(
        'waitlist_signups',
        sa.Column('consent_marketing', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        schema='bc_legal_ds'
    )
    op.add_column(
        'waitlist_signups',
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=True),
        schema='bc_legal_ds'
    )


def downgrade() -> None:
    # Remove CASL consent tracking fields
    op.drop_column('waitlist_signups', 'consent_date', schema='bc_legal_ds')
    op.drop_column('waitlist_signups', 'consent_marketing', schema='bc_legal_ds')
