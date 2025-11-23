"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 23/11/2025
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial tables: code_reviews and agent_findings"""
    # Create code_reviews table
    op.create_table(
        'code_reviews',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create agent_findings table
    op.create_table(
        'agent_findings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code_review_id', sa.Integer(), sa.ForeignKey('code_reviews.id'), nullable=False),
        sa.Column('agent_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('issue_type', sa.String(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
    )


def downgrade():
    """Drop tables: agent_findings and code_reviews"""
    # Drop agent_findings table
    op.drop_table('agent_findings')
    # Dr op code_reviews table
    op.drop_table('code_reviews')
