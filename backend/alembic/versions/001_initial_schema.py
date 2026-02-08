"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create brands table
    op.create_table(
        'brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=True),
        sa.Column('cuisine_type', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_brands_name'), 'brands', ['name'], unique=True)

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('total_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_spend', sa.DECIMAL(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('first_order_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_order_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('external_id')
    )
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=True)
    op.create_index(op.f('ix_customers_external_id'), 'customers', ['external_id'], unique=True)

    # Create menu_items table
    op.create_table(
        'menu_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('cuisine_type', sa.String(length=100), nullable=True),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('dietary_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('flavor_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_items_brand_id'), 'menu_items', ['brand_id'], unique=False)

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_amount', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )
    op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_orders_brand_id'), 'orders', ['brand_id'], unique=False)
    op.create_index(op.f('ix_orders_order_date'), 'orders', ['order_date'], unique=False)
    op.create_index(op.f('ix_orders_external_id'), 'orders', ['external_id'], unique=True)

    # Create customer_preferences table
    op.create_table(
        'customer_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('favorite_cuisines', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('favorite_categories', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dietary_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('price_sensitivity', sa.String(length=20), nullable=True),
        sa.Column('order_frequency', sa.String(length=20), nullable=True),
        sa.Column('brand_affinity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_order_times', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_computed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )
    op.create_index(op.f('ix_customer_preferences_customer_id'), 'customer_preferences', ['customer_id'], unique=True)

    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('subtotal', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_menu_item_id'), 'order_items', ['menu_item_id'], unique=False)

    # Create ingestion_jobs table
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('csv_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_rows', sa.Integer(), nullable=True),
        sa.Column('processed_rows', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_rows', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('validation_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ingestion_jobs')
    op.drop_table('order_items')
    op.drop_table('customer_preferences')
    op.drop_table('orders')
    op.drop_table('menu_items')
    op.drop_table('customers')
    op.drop_table('brands')
