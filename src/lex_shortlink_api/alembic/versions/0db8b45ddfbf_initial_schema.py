"""Initial schema

Revision ID: 0db8b45ddfbf
Revises: 
Create Date: 2026-07-12 01:30:52.962302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0db8b45ddfbf'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('key_hash', sa.Text(), unique=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
      )

    # Create links table
    op.create_table(
        'links',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('slug', sa.Text(), unique=True, nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('api_key_id', sa.UUID(), sa.ForeignKey('api_keys.id'), nullable=True),
      )

    # Create click_events table
    op.create_table(
        'click_events',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('link_id', sa.UUID(), sa.ForeignKey('links.id'), nullable=False),
        sa.Column('clicked_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('country_code', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('device_type', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
      )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('click_events')
    op.drop_table('links')
    op.drop_table('api_keys')