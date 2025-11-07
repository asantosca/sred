"""Rename case_type to matter_type in matters table

Revision ID: 3a06c0baabeb
Revises: 9847e9d42908
Create Date: 2025-11-06 18:56:28.947758

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a06c0baabeb'
down_revision = '9847e9d42908'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename column case_type to matter_type in matters table
    op.alter_column('matters', 'case_type', new_column_name='matter_type')


def downgrade() -> None:
    # Rename column matter_type back to case_type
    op.alter_column('matters', 'matter_type', new_column_name='case_type')