"""add_project_context_fields_to_claims

Revision ID: a2b3c4d5e6f7
Revises: 89a9a5b9c924
Create Date: 2026-01-16 12:00:00.000000

Add project-specific fields to claims table to guide AI in T661 generation:
- project_title: Short name for the specific R&D project
- project_objective: Technical goal description (1-2 sentences)
- technology_focus: Specific technology area and keywords

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = '89a9a5b9c924'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add project context fields to claims table
    op.add_column('claims', sa.Column('project_title', sa.String(255), nullable=True),
                  schema='bc_legal_ds')
    op.add_column('claims', sa.Column('project_objective', sa.Text(), nullable=True),
                  schema='bc_legal_ds')
    op.add_column('claims', sa.Column('technology_focus', sa.String(500), nullable=True),
                  schema='bc_legal_ds')


def downgrade() -> None:
    op.drop_column('claims', 'technology_focus', schema='bc_legal_ds')
    op.drop_column('claims', 'project_objective', schema='bc_legal_ds')
    op.drop_column('claims', 'project_title', schema='bc_legal_ds')
