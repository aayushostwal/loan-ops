"""add_lender_model

Revision ID: 3a4b5c6d7e8f
Revises: 2118a2715dde
Create Date: 2025-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3a4b5c6d7e8f'
down_revision: Union[str, Sequence[str], None] = '2118a2715dde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create lenders table."""
    op.create_table(
        'lenders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lender_name', sa.String(length=255), nullable=False, comment='Name of the lender'),
        sa.Column('policy_details', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Structured policy details extracted from the document'),
        sa.Column('raw_data', sa.Text(), nullable=True, comment='Raw OCR text extracted from PDF document'),
        sa.Column('processed_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Processed and structured data from LLM'),
        sa.Column('status', sa.Enum('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED', name='lenderstatus'), nullable=False, comment='Current processing status of the document'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='User who created this record'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when record was last updated'),
        sa.Column('original_filename', sa.String(length=500), nullable=True, comment='Original PDF filename'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lenders_id'), 'lenders', ['id'], unique=False)
    op.create_index(op.f('ix_lenders_lender_name'), 'lenders', ['lender_name'], unique=False)
    op.create_index(op.f('ix_lenders_status'), 'lenders', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Drop lenders table."""
    op.drop_index(op.f('ix_lenders_status'), table_name='lenders')
    op.drop_index(op.f('ix_lenders_lender_name'), table_name='lenders')
    op.drop_index(op.f('ix_lenders_id'), table_name='lenders')
    op.drop_table('lenders')
    op.execute('DROP TYPE lenderstatus')

