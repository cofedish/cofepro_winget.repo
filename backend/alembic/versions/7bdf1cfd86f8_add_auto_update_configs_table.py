"""Add auto_update_configs table

Revision ID: 7bdf1cfd86f8
Revises: 001
Create Date: 2025-10-17 16:52:06.470026

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7bdf1cfd86f8'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create auto_update_configs table
    op.create_table(
        'auto_update_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('architectures', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('installer_types', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('max_versions', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_sync_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['package_id'], ['packages.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('package_id')
    )

    # Create indexes
    op.create_index('idx_auto_update_package_id', 'auto_update_configs', ['package_id'])
    op.create_index('idx_auto_update_enabled', 'auto_update_configs', ['enabled'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_auto_update_enabled', table_name='auto_update_configs')
    op.drop_index('idx_auto_update_package_id', table_name='auto_update_configs')

    # Drop table
    op.drop_table('auto_update_configs')
