"""
Auto-update configuration endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import AutoUpdateConfig, Package, UserRole
from app.schemas import (
    AutoUpdateConfigCreate,
    AutoUpdateConfigUpdate,
    AutoUpdateConfigResponse,
    PackageWithAutoUpdate
)
from app.security import get_current_user, require_role

router = APIRouter(prefix="/api/admin/auto-update", tags=["auto-update"])


@router.get("/configs", response_model=List[PackageWithAutoUpdate])
async def list_auto_update_configs(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.MAINTAINER))
):
    """Get all packages with auto-update configurations"""
    query = select(Package).options(selectinload(Package.auto_update_config))
    
    if enabled_only:
        query = query.join(AutoUpdateConfig).where(AutoUpdateConfig.enabled == True)
    
    result = await db.execute(query)
    packages = result.scalars().all()
    
    return packages


@router.get("/configs/{package_id}", response_model=AutoUpdateConfigResponse)
async def get_auto_update_config(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.MAINTAINER))
):
    """Get auto-update config for specific package"""
    result = await db.execute(
        select(AutoUpdateConfig).where(AutoUpdateConfig.package_id == package_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Auto-update config not found")
    
    return config


@router.post("/configs", response_model=AutoUpdateConfigResponse, status_code=201)
async def create_auto_update_config(
    config_data: AutoUpdateConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.MAINTAINER))
):
    """Enable auto-update for a package"""
    # Check if package exists
    result = await db.execute(
        select(Package).where(Package.id == config_data.package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Check if config already exists
    result = await db.execute(
        select(AutoUpdateConfig).where(AutoUpdateConfig.package_id == config_data.package_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=409, detail="Auto-update config already exists for this package")
    
    # Create config
    config = AutoUpdateConfig(
        package_id=config_data.package_id,
        enabled=config_data.enabled,
        architectures=config_data.architectures,
        installer_types=config_data.installer_types,
        max_versions=config_data.max_versions
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return config


@router.put("/configs/{package_id}", response_model=AutoUpdateConfigResponse)
async def update_auto_update_config(
    package_id: int,
    config_data: AutoUpdateConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.MAINTAINER))
):
    """Update auto-update configuration"""
    result = await db.execute(
        select(AutoUpdateConfig).where(AutoUpdateConfig.package_id == package_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Auto-update config not found")
    
    # Update fields
    if config_data.enabled is not None:
        config.enabled = config_data.enabled
    if config_data.architectures is not None:
        config.architectures = config_data.architectures
    if config_data.installer_types is not None:
        config.installer_types = config_data.installer_types
    if config_data.max_versions is not None:
        config.max_versions = config_data.max_versions
    
    await db.commit()
    await db.refresh(config)
    
    return config


@router.delete("/configs/{package_id}", status_code=204)
async def delete_auto_update_config(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN))
):
    """Disable auto-update for a package (delete config)"""
    result = await db.execute(
        delete(AutoUpdateConfig).where(AutoUpdateConfig.package_id == package_id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Auto-update config not found")
    
    await db.commit()
    return None
