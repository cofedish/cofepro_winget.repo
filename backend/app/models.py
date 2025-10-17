"""
SQLAlchemy ORM models
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    BigInteger, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles"""
    ADMIN = "admin"
    MAINTAINER = "maintainer"
    VIEWER = "viewer"
    SERVICE = "service"


class InstallerType(str, enum.Enum):
    """Installer types"""
    EXE = "exe"
    MSI = "msi"
    MSIX = "msix"
    APPX = "appx"
    ZIP = "zip"
    INNO = "inno"
    NULLSOFT = "nullsoft"
    WIX = "wix"
    BURN = "burn"
    PORTABLE = "portable"


class Architecture(str, enum.Enum):
    """Architectures"""
    X86 = "x86"
    X64 = "x64"
    ARM = "arm"
    ARM64 = "arm64"
    NEUTRAL = "neutral"


class InstallerScope(str, enum.Enum):
    """Installer scope"""
    USER = "user"
    MACHINE = "machine"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="actor_rel", foreign_keys="AuditLog.actor_id")


class Package(Base):
    """Package model"""
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), unique=True, index=True, nullable=False)  # e.g., "7zip.7zip"
    name = Column(String(255), nullable=False)  # e.g., "7-Zip"
    publisher = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    homepage_url = Column(String(500), nullable=True)
    license = Column(String(255), nullable=True)
    license_url = Column(String(500), nullable=True)
    copyright = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    is_active = Column(Boolean, default=True, nullable=False)
    is_mirrored = Column(Boolean, default=False, nullable=False)  # True if from updater
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    versions = relationship("Version", back_populates="package", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_package_identifier", "identifier"),
        Index("idx_package_is_active", "is_active"),
    )


class Version(Base):
    """Package version model"""
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(100), nullable=False)  # e.g., "23.01"
    release_notes = Column(Text, nullable=True)
    release_notes_url = Column(String(500), nullable=True)
    release_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    package = relationship("Package", back_populates="versions")
    installers = relationship("Installer", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_version_package_id", "package_id"),
        Index("idx_version_package_version", "package_id", "version", unique=True),
    )


class Installer(Base):
    """Installer model"""
    __tablename__ = "installers"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("versions.id", ondelete="CASCADE"), nullable=False)
    architecture = Column(SQLEnum(Architecture, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    installer_type = Column(SQLEnum(InstallerType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    scope = Column(SQLEnum(InstallerScope, values_callable=lambda obj: [e.value for e in obj]), nullable=True)

    # File information
    s3_key = Column(String(500), nullable=False)  # S3 object key
    file_name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)

    # Installer metadata
    installer_url = Column(String(1000), nullable=False)  # Our URL for serving
    silent_switches = Column(String(500), nullable=True)
    silent_with_progress_switches = Column(String(500), nullable=True)
    product_code = Column(String(100), nullable=True)
    minimum_os_version = Column(String(50), nullable=True)

    # MSIX-specific
    signature_sha256 = Column(String(64), nullable=True)
    package_family_name = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    version = relationship("Version", back_populates="installers")

    __table_args__ = (
        Index("idx_installer_version_id", "version_id"),
        Index("idx_installer_sha256", "sha256"),
    )


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_username = Column(String(100), nullable=False)  # Denormalized for history
    action = Column(String(100), nullable=False)  # e.g., "create", "update", "delete", "upload"
    entity_type = Column(String(50), nullable=False)  # e.g., "package", "version", "installer"
    entity_id = Column(Integer, nullable=True)
    entity_identifier = Column(String(255), nullable=True)  # Package identifier for context
    meta = Column("metadata", JSON, nullable=True)  # Additional context (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    actor_rel = relationship("User", back_populates="audit_logs", foreign_keys=[actor_id])

    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_actor", "actor_id"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
    )


class RefreshToken(Base):
    """Refresh token model"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_refresh_token_hash", "token_hash"),
        Index("idx_refresh_token_user_id", "user_id"),
    )


class AutoUpdateConfig(Base):
    """Auto-update configuration for packages"""
    __tablename__ = "auto_update_configs"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Update settings
    enabled = Column(Boolean, default=True, nullable=False)
    architectures = Column(JSON, nullable=False, default=list)  # ["x64", "x86", "arm64"]
    installer_types = Column(JSON, nullable=False, default=list)  # ["exe", "msi"]
    max_versions = Column(Integer, default=1, nullable=False)  # Keep N latest versions

    # Last sync info
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(50), nullable=True)  # "success", "failed", "partial"
    last_sync_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    package = relationship("Package", backref="auto_update_config")

    __table_args__ = (
        Index("idx_auto_update_package_id", "package_id"),
        Index("idx_auto_update_enabled", "enabled"),
    )
