"""Add campaigns tables

Revision ID: 002
Revises: 001
Create Date: 2024-02-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=True, comment='Campaign purpose used in message generation prompt'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft',
                  comment='draft | previewing | ready | executing | completed | failed'),
        sa.Column('segment_filters', postgresql.JSON(astext_type=sa.Text()), nullable=True,
                  comment='Filter criteria used to select recipients'),
        sa.Column('total_recipients', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('generated_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of messages generated so far'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaigns_status'), 'campaigns', ['status'])
    op.create_index(op.f('ix_campaigns_created_at'), 'campaigns', ['created_at'])

    # Create campaign_recipients table
    op.create_table(
        'campaign_recipients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_message', postgresql.JSON(astext_type=sa.Text()), nullable=True,
                  comment='Generated message with subject and body'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending',
                  comment='pending | generated | failed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaign_recipients_campaign_id'), 'campaign_recipients', ['campaign_id'])
    op.create_index(op.f('ix_campaign_recipients_customer_id'), 'campaign_recipients', ['customer_id'])
    op.create_index(op.f('ix_campaign_recipients_status'), 'campaign_recipients', ['status'])


def downgrade() -> None:
    op.drop_index(op.f('ix_campaign_recipients_status'), table_name='campaign_recipients')
    op.drop_index(op.f('ix_campaign_recipients_customer_id'), table_name='campaign_recipients')
    op.drop_index(op.f('ix_campaign_recipients_campaign_id'), table_name='campaign_recipients')
    op.drop_table('campaign_recipients')

    op.drop_index(op.f('ix_campaigns_created_at'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_status'), table_name='campaigns')
    op.drop_table('campaigns')
