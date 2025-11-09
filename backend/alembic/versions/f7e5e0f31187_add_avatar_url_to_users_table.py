"""Add profile_picture to users table

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
    # Rename avatar_url column to profile_picture
    op.alter_column('users', 'avatar_url', new_column_name='profile_picture')


def downgrade() -> None:
    # Rename profile_picture column back to avatar_url
    op.alter_column('users', 'profile_picture', new_column_name='avatar_url')