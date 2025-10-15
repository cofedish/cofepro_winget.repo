"""
Admin API routes for managing packages, versions, installers
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Package, Version, Installer, User, UserRole, AuditLog
from app.schemas import (
    PackageCreate, PackageUpdate, PackageResponse, PackageWithVersions,
    VersionCreate, VersionUpdate, VersionResponse, VersionWithInstallers,
    InstallerCreate, InstallerUpdate, InstallerResponse,
    UserCreate, UserUpdate, UserResponse,
    AuditLogResponse, DashboardStats
)
from app.security import require_role, get_current_user, hash_password
from app.utils import create_audit_log
from app.s3 import s3_client

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== Package Management ====================

@router.get("/packages", response_model=List[PackageResponse])
async def list_packages(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_mirrored: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.VIEWER))
):
    """
    List all packages with optional filtering
    """
    query = select(Package)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            Package.identifier.ilike(search_pattern) |
            Package.name.ilike(search_pattern) |
            Package.publisher.ilike(search_pattern)
        )

    if is_mirrored is not None:
        query = query.where(Package.is_mirrored == is_mirrored)

    query = query.order_by(Package.identifier).offset(skip).limit(limit)

    result = await db.execute(query)
    packages = result.scalars().all()
    return packages


@router.get("/packages/{package_id}", response_model=PackageWithVersions)
async def get_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.VIEWER))
):
    """
    Get package by ID with versions
    """
    result = await db.execute(
        select(Package)
        .where(Package.id == package_id)
        .options(
            selectinload(Package.versions).selectinload(Version.installers)
        )
    )
    package = result.scalar_one_or_none()

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )

    return package


@router.post("/packages", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    package_data: PackageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Create new package
    """
    # Check if package with identifier already exists
    result = await db.execute(
        select(Package).where(Package.identifier == package_data.identifier)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Package with identifier {package_data.identifier} already exists"
        )

    # Create package
    package = Package(**package_data.model_dump())
    db.add(package)
    await db.commit()
    await db.refresh(package)

    # Audit log
    await create_audit_log(
        db, current_user, "create", "package",
        entity_id=package.id,
        entity_identifier=package.identifier,
        request=request
    )

    return package


@router.put("/packages/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: int,
    package_data: PackageUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Update package
    """
    result = await db.execute(select(Package).where(Package.id == package_id))
    package = result.scalar_one_or_none()

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )

    # Update fields
    update_data = package_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(package, field, value)

    await db.commit()
    await db.refresh(package)

    # Audit log
    await create_audit_log(
        db, current_user, "update", "package",
        entity_id=package.id,
        entity_identifier=package.identifier,
        meta=update_data,
        request=request
    )

    return package


@router.delete("/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Delete package (admin only)
    """
    result = await db.execute(
        select(Package)
        .where(Package.id == package_id)
        .options(selectinload(Package.versions).selectinload(Version.installers))
    )
    package = result.scalar_one_or_none()

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )

    package_identifier = package.identifier

    # Delete associated files from S3
    for version in package.versions:
        for installer in version.installers:
            try:
                s3_client.delete_file(installer.s3_key)
            except Exception as e:
                # Log error but continue
                pass

    # Delete from database (cascade will handle versions and installers)
    await db.delete(package)
    await db.commit()

    # Audit log
    await create_audit_log(
        db, current_user, "delete", "package",
        entity_identifier=package_identifier,
        request=request
    )

    return None


# ==================== Version Management ====================

@router.get("/versions/{version_id}", response_model=VersionWithInstallers)
async def get_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.VIEWER))
):
    """
    Get version by ID with installers
    """
    result = await db.execute(
        select(Version)
        .where(Version.id == version_id)
        .options(selectinload(Version.installers))
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )

    return version


@router.post("/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    version_data: VersionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Create new version
    """
    # Check if package exists
    result = await db.execute(select(Package).where(Package.id == version_data.package_id))
    package = result.scalar_one_or_none()

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )

    # Check if version already exists
    result = await db.execute(
        select(Version).where(
            Version.package_id == version_data.package_id,
            Version.version == version_data.version
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version {version_data.version} already exists for this package"
        )

    # Create version
    version = Version(**version_data.model_dump())
    db.add(version)
    await db.commit()
    await db.refresh(version)

    # Audit log
    await create_audit_log(
        db, current_user, "create", "version",
        entity_id=version.id,
        entity_identifier=package.identifier,
        meta={"version": version.version},
        request=request
    )

    return version


@router.put("/versions/{version_id}", response_model=VersionResponse)
async def update_version(
    version_id: int,
    version_data: VersionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Update version
    """
    result = await db.execute(
        select(Version)
        .where(Version.id == version_id)
        .options(selectinload(Version.package))
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )

    # Update fields
    update_data = version_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(version, field, value)

    await db.commit()
    await db.refresh(version)

    # Audit log
    await create_audit_log(
        db, current_user, "update", "version",
        entity_id=version.id,
        entity_identifier=version.package.identifier,
        meta={"version": version.version, **update_data},
        request=request
    )

    return version


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Delete version (admin only)
    """
    result = await db.execute(
        select(Version)
        .where(Version.id == version_id)
        .options(selectinload(Version.installers), selectinload(Version.package))
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )

    package_identifier = version.package.identifier
    version_str = version.version

    # Delete associated files from S3
    for installer in version.installers:
        try:
            s3_client.delete_file(installer.s3_key)
        except Exception:
            pass

    # Delete from database
    await db.delete(version)
    await db.commit()

    # Audit log
    await create_audit_log(
        db, current_user, "delete", "version",
        entity_identifier=package_identifier,
        meta={"version": version_str},
        request=request
    )

    return None


# ==================== Installer Management ====================

@router.get("/installers/{installer_id}", response_model=InstallerResponse)
async def get_installer(
    installer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.VIEWER))
):
    """
    Get installer by ID
    """
    result = await db.execute(select(Installer).where(Installer.id == installer_id))
    installer = result.scalar_one_or_none()

    if not installer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installer not found"
        )

    return installer


@router.put("/installers/{installer_id}", response_model=InstallerResponse)
async def update_installer(
    installer_id: int,
    installer_data: InstallerUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Update installer metadata
    """
    result = await db.execute(
        select(Installer)
        .where(Installer.id == installer_id)
        .options(
            selectinload(Installer.version).selectinload(Version.package)
        )
    )
    installer = result.scalar_one_or_none()

    if not installer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installer not found"
        )

    # Update fields
    update_data = installer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(installer, field, value)

    await db.commit()
    await db.refresh(installer)

    # Audit log
    await create_audit_log(
        db, current_user, "update", "installer",
        entity_id=installer.id,
        entity_identifier=installer.version.package.identifier,
        meta=update_data,
        request=request
    )

    return installer


@router.delete("/installers/{installer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_installer(
    installer_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Delete installer (admin only)
    """
    result = await db.execute(
        select(Installer)
        .where(Installer.id == installer_id)
        .options(
            selectinload(Installer.version).selectinload(Version.package)
        )
    )
    installer = result.scalar_one_or_none()

    if not installer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installer not found"
        )

    package_identifier = installer.version.package.identifier
    s3_key = installer.s3_key

    # Delete from S3
    try:
        s3_client.delete_file(s3_key)
    except Exception:
        pass

    # Delete from database
    await db.delete(installer)
    await db.commit()

    # Audit log
    await create_audit_log(
        db, current_user, "delete", "installer",
        entity_identifier=package_identifier,
        meta={"s3_key": s3_key},
        request=request
    )

    return None


# ==================== User Management ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    List all users (admin only)
    """
    result = await db.execute(
        select(User).order_by(User.username).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Create new user (admin only)
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists"
        )

    # Create user
    user_dict = user_data.model_dump()
    password = user_dict.pop("password")
    password_hash = hash_password(password)

    user = User(**user_dict, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Audit log
    await create_audit_log(
        db, current_user, "create", "user",
        entity_id=user.id,
        meta={"username": user.username, "role": user.role.value},
        request=request
    )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Update user (admin only)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data:
        password = update_data.pop("password")
        update_data["password_hash"] = hash_password(password)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    # Audit log
    await create_audit_log(
        db, current_user, "update", "user",
        entity_id=user.id,
        meta={"username": user.username},
        request=request
    )

    return user


# ==================== Dashboard & Statistics ====================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.VIEWER))
):
    """
    Get dashboard statistics
    """
    # Count packages
    result = await db.execute(select(func.count(Package.id)))
    total_packages = result.scalar()

    # Count mirrored packages
    result = await db.execute(
        select(func.count(Package.id)).where(Package.is_mirrored == True)
    )
    mirrored_packages = result.scalar()

    # Count versions
    result = await db.execute(select(func.count(Version.id)))
    total_versions = result.scalar()

    # Count installers
    result = await db.execute(select(func.count(Installer.id)))
    total_installers = result.scalar()

    # Sum installer sizes
    result = await db.execute(select(func.sum(Installer.size_bytes)))
    total_size = result.scalar() or 0

    # Count recent updates (last 7 days)
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(func.count(Package.id)).where(Package.updated_at >= seven_days_ago)
    )
    recent_updates = result.scalar()

    return DashboardStats(
        total_packages=total_packages,
        total_versions=total_versions,
        total_installers=total_installers,
        total_size_bytes=total_size,
        mirrored_packages=mirrored_packages,
        manual_packages=total_packages - mirrored_packages,
        recent_updates=recent_updates
    )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Get audit logs (admin only)
    """
    query = select(AuditLog)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)

    if action:
        query = query.where(AuditLog.action == action)

    query = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()
    return logs
