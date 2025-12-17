"""add description column to documents

Revision ID: 2a8b383d4a6b
Revises: 904accf57229
Create Date: 2025-12-10 15:57:03.504217

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a8b383d4a6b'
down_revision = '904accf57229'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('description', sa.Text(), nullable=True), schema='bc_legal_ds')


def downgrade() -> None:
    op.drop_column('documents', 'description', schema='bc_legal_ds')
