"""add loan application models

Revision ID: 4c5d6e7f8g9h
Revises: 3a4b5c6d7e8f
Create Date: 2025-12-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4c5d6e7f8g9h'
down_revision: Union[str, None] = '3a4b5c6d7e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create loan_applications table
    op.create_table(
        'loan_applications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('applicant_name', sa.String(length=255), nullable=False, comment='Name of the applicant'),
        sa.Column('applicant_email', sa.String(length=255), nullable=True, comment='Email of the applicant'),
        sa.Column('applicant_phone', sa.String(length=50), nullable=True, comment='Phone number of the applicant'),
        sa.Column('application_details', postgresql.JSON(astext_type=sa.Text()), nullable=True, 
                  comment='Structured application details extracted from the document'),
        sa.Column('raw_data', sa.Text(), nullable=True, 
                  comment='Raw OCR text extracted from PDF document'),
        sa.Column('processed_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, 
                  comment='Processed and structured data from LLM'),
        sa.Column('status', sa.Enum('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED', 
                                    name='applicationstatus'), nullable=False, 
                  comment='Current processing status of the application'),
        sa.Column('workflow_run_id', sa.String(length=255), nullable=True, 
                  comment='Hatchet workflow run ID for tracking'),
        sa.Column('created_by', sa.String(length=255), nullable=True, 
                  comment='User who created this record'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), 
                  nullable=False, comment='Timestamp when record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), 
                  nullable=False, comment='Timestamp when record was last updated'),
        sa.Column('original_filename', sa.String(length=500), nullable=True, 
                  comment='Original PDF filename'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for loan_applications
    op.create_index(op.f('ix_loan_applications_id'), 'loan_applications', ['id'], unique=False)
    op.create_index(op.f('ix_loan_applications_applicant_name'), 'loan_applications', ['applicant_name'], unique=False)
    op.create_index(op.f('ix_loan_applications_status'), 'loan_applications', ['status'], unique=False)
    
    # Create loan_matches table
    op.create_table(
        'loan_matches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('loan_application_id', sa.Integer(), nullable=False, 
                  comment='Reference to loan application'),
        sa.Column('lender_id', sa.Integer(), nullable=False, 
                  comment='Reference to lender'),
        sa.Column('match_score', sa.Float(), nullable=True, 
                  comment='Match score between 0-100 (higher is better)'),
        sa.Column('match_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True, 
                  comment='Detailed analysis of matching criteria'),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 
                                    name='matchstatus'), nullable=False, 
                  comment='Current processing status of the match'),
        sa.Column('error_message', sa.Text(), nullable=True, 
                  comment='Error message if matching failed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), 
                  nullable=False, comment='Timestamp when record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), 
                  nullable=False, comment='Timestamp when record was last updated'),
        sa.ForeignKeyConstraint(['lender_id'], ['lenders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['loan_application_id'], ['loan_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for loan_matches
    op.create_index(op.f('ix_loan_matches_id'), 'loan_matches', ['id'], unique=False)
    op.create_index(op.f('ix_loan_matches_loan_application_id'), 'loan_matches', ['loan_application_id'], unique=False)
    op.create_index(op.f('ix_loan_matches_lender_id'), 'loan_matches', ['lender_id'], unique=False)
    op.create_index(op.f('ix_loan_matches_status'), 'loan_matches', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes for loan_matches
    op.drop_index(op.f('ix_loan_matches_status'), table_name='loan_matches')
    op.drop_index(op.f('ix_loan_matches_lender_id'), table_name='loan_matches')
    op.drop_index(op.f('ix_loan_matches_loan_application_id'), table_name='loan_matches')
    op.drop_index(op.f('ix_loan_matches_id'), table_name='loan_matches')
    
    # Drop loan_matches table
    op.drop_table('loan_matches')
    
    # Drop indexes for loan_applications
    op.drop_index(op.f('ix_loan_applications_status'), table_name='loan_applications')
    op.drop_index(op.f('ix_loan_applications_applicant_name'), table_name='loan_applications')
    op.drop_index(op.f('ix_loan_applications_id'), table_name='loan_applications')
    
    # Drop loan_applications table
    op.drop_table('loan_applications')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS matchstatus')
    op.execute('DROP TYPE IF EXISTS applicationstatus')

