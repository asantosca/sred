"""Add avatar_url to users table

Revision ID: f7e5e0f31187
Revises: 3a06c0baabeb
Create Date: 2025-11-08 20:06:17.451518

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7e5e0f31187'
down_revision = '3a06c0baabeb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add avatar_url column to users table
    op.add_column('users', sa.Column('avatar_url', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove avatar_url column from users table
    op.drop_column('users', 'avatar_url')