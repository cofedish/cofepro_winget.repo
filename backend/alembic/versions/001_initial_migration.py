"""initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Note: Enum types are created automatically by SQLAlchemy when op.create_table() is called
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'maintainer', 'viewer', 'service', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # Packages table
    op.create_table(
        'packages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('publisher', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('homepage_url', sa.String(length=500), nullable=True),
        sa.Column('license', sa.String(length=255), nullable=True),
        sa.Column('license_url', sa.String(length=500), nullable=True),
        sa.Column('copyright', sa.String(length=500), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_mirrored', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_package_identifier', 'packages', ['identifier'], unique=True)
    op.create_index('idx_package_is_active', 'packages', ['is_active'])

    # Versions table
    op.create_table(
        'versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),
        sa.Column('release_notes', sa.Text(), nullable=True),
        sa.Column('release_notes_url', sa.String(length=500), nullable=True),
        sa.Column('release_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['package_id'], ['packages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_version_package_id', 'versions', ['package_id'])
    op.create_index('idx_version_package_version', 'versions', ['package_id', 'version'], unique=True)

    # Installers table
    op.create_table(
        'installers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('architecture', postgresql.ENUM('x86', 'x64', 'arm', 'arm64', 'neutral', name='architecture'), nullable=False),
        sa.Column('installer_type', postgresql.ENUM('exe', 'msi', 'msix', 'appx', 'zip', 'inno', 'nullsoft', 'wix', 'burn', 'portable', name='installertype'), nullable=False),
        sa.Column('scope', postgresql.ENUM('user', 'machine', name='installerscope'), nullable=True),
        sa.Column('s3_key', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('installer_url', sa.String(length=1000), nullable=False),
        sa.Column('silent_switches', sa.String(length=500), nullable=True),
        sa.Column('silent_with_progress_switches', sa.String(length=500), nullable=True),
        sa.Column('product_code', sa.String(length=100), nullable=True),
        sa.Column('minimum_os_version', sa.String(length=50), nullable=True),
        sa.Column('signature_sha256', sa.String(length=64), nullable=True),
        sa.Column('package_family_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['version_id'], ['versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_installer_version_id', 'installers', ['version_id'])
    op.create_index('idx_installer_sha256', 'installers', ['sha256'])

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_username', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('entity_identifier', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_actor', 'audit_logs', ['actor_id'])
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])

    # Refresh tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_refresh_token_hash', 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index('idx_refresh_token_user_id', 'refresh_tokens', ['user_id'])


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('audit_logs')
    op.drop_table('installers')
    op.drop_table('versions')
    op.drop_table('packages')
    op.drop_table('users')

    op.execute('DROP TYPE IF EXISTS installerscope')
    op.execute('DROP TYPE IF EXISTS architecture')
    op.execute('DROP TYPE IF EXISTS installertype')
    op.execute('DROP TYPE IF EXISTS userrole')
