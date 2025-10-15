"""
WinGet REST Source API endpoints
Microsoft.Rest compatible endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Package, Version, Installer
from app.schemas import (
    WinGetInformation, WinGetSearchRequest, WinGetSearchResponse,
    WinGetSearchMatch, WinGetVersion, WinGetVersionsResponse,
    WinGetManifestResponse, WinGetManifest, WinGetInstaller,
    WinGetInstallerSwitches
)
from app.config import settings

router = APIRouter(tags=["WinGet REST API"])


@router.get("/information", response_model=WinGetInformation)
async def get_information():
    """
    WinGet information endpoint
    Required by winget client to verify source compatibility
    """
    return WinGetInformation(
        Data={
            "SourceIdentifier": "Private.WinGet.Source",
            "ServerSupportedVersions": ["1.0.0", "1.1.0", "1.4.0", "1.5.0", "1.6.0", "1.7.0"]
        }
    )


@router.post("/manifestSearch", response_model=WinGetSearchResponse)
async def manifest_search(
    search_request: WinGetSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search for packages
    Main endpoint used by winget search command
    """
    query = select(Package).where(Package.is_active == True)

    # Handle search query
    if search_request.Query:
        keyword = search_request.Query.get("KeyWord", "")
        match_type = search_request.Query.get("MatchType", "Substring")

        if keyword:
            if match_type == "Exact":
                query = query.where(
                    or_(
                        Package.identifier == keyword,
                        Package.name == keyword
                    )
                )
            elif match_type == "Substring":
                search_pattern = f"%{keyword}%"
                query = query.where(
                    or_(
                        Package.identifier.ilike(search_pattern),
                        Package.name.ilike(search_pattern),
                        Package.publisher.ilike(search_pattern),
                        Package.description.ilike(search_pattern)
                    )
                )
            elif match_type == "StartsWith":
                search_pattern = f"{keyword}%"
                query = query.where(
                    or_(
                        Package.identifier.ilike(search_pattern),
                        Package.name.ilike(search_pattern)
                    )
                )

    # Handle inclusions (package identifier filter)
    if search_request.Inclusions:
        identifiers = []
        for inclusion in search_request.Inclusions:
            if "PackageIdentifier" in inclusion:
                identifiers.append(inclusion["PackageIdentifier"])
        if identifiers:
            query = query.where(Package.identifier.in_(identifiers))

    # Apply maximum results limit
    max_results = search_request.MaximumResults or 100
    query = query.limit(max_results)

    # Eager load versions
    query = query.options(selectinload(Package.versions).selectinload(Version.installers))

    # Execute query
    result = await db.execute(query)
    packages = result.scalars().all()

    # Build response
    matches = []
    for package in packages:
        # Get active versions
        active_versions = [v for v in package.versions if v.is_active]

        if not active_versions:
            continue

        # Build version list
        version_list = []
        for version in active_versions:
            winget_version = WinGetVersion(
                PackageVersion=version.version,
                Channel=None
            )
            version_list.append(winget_version)

        match = WinGetSearchMatch(
            PackageIdentifier=package.identifier,
            PackageName=package.name,
            Publisher=package.publisher,
            Versions=version_list
        )
        matches.append(match)

    return WinGetSearchResponse(Data=matches)


@router.get("/packageVersions/{package_identifier}", response_model=WinGetVersionsResponse)
async def get_package_versions(
    package_identifier: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all versions of a package
    """
    # Find package
    result = await db.execute(
        select(Package)
        .where(Package.identifier == package_identifier)
        .options(selectinload(Package.versions))
    )
    package = result.scalar_one_or_none()

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package {package_identifier} not found"
        )

    # Build version list
    version_list = []
    for version in package.versions:
        if version.is_active:
            winget_version = WinGetVersion(
                PackageVersion=version.version,
                Channel=None
            )
            version_list.append(winget_version)

    return WinGetVersionsResponse(Data=version_list)


@router.get("/packageManifests/{package_identifier}", response_model=WinGetManifestResponse)
async def get_package_manifest_latest(
    package_identifier: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get manifest for latest version of package
    """
    # Find package with versions
    result = await db.execute(
        select(Package)
        .where(Package.identifier == package_identifier)
        .options(selectinload(Package.versions).selectinload(Version.installers))
    )
    package = result.scalar_one_or_none()

    if not package or not package.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package {package_identifier} not found"
        )

    # Get latest active version
    active_versions = [v for v in package.versions if v.is_active]
    if not active_versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active versions for package {package_identifier}"
        )

    # Sort by version (simple string sort, could be improved with semantic versioning)
    latest_version = sorted(active_versions, key=lambda v: v.version, reverse=True)[0]

    # Build manifest
    manifest = await build_manifest(package, latest_version)
    return WinGetManifestResponse(Data=manifest)


@router.get("/packageManifests/{package_identifier}/{version}", response_model=WinGetManifestResponse)
async def get_package_manifest_version(
    package_identifier: str,
    version: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get manifest for specific version of package
    """
    # Find package and version
    result = await db.execute(
        select(Package)
        .where(Package.identifier == package_identifier)
        .options(selectinload(Package.versions).selectinload(Version.installers))
    )
    package = result.scalar_one_or_none()

    if not package or not package.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package {package_identifier} not found"
        )

    # Find specific version
    target_version = None
    for v in package.versions:
        if v.version == version and v.is_active:
            target_version = v
            break

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for package {package_identifier}"
        )

    # Build manifest
    manifest = await build_manifest(package, target_version)
    return WinGetManifestResponse(Data=manifest)


async def build_manifest(package: Package, version: Version) -> WinGetManifest:
    """
    Build WinGet manifest from package and version
    """
    # Build installers list
    installers = []
    for installer in version.installers:
        if not installer.is_active:
            continue

        # Map our architecture enum to WinGet format
        arch_map = {
            "x86": "x86",
            "x64": "x64",
            "arm": "arm",
            "arm64": "arm64",
            "neutral": "neutral"
        }

        # Map installer type
        type_map = {
            "exe": "exe",
            "msi": "msi",
            "msix": "msix",
            "appx": "appx",
            "zip": "zip",
            "inno": "inno",
            "nullsoft": "nullsoft",
            "wix": "wix",
            "burn": "burn",
            "portable": "portable"
        }

        # Build installer switches
        installer_switches = None
        if installer.silent_switches or installer.silent_with_progress_switches:
            installer_switches = WinGetInstallerSwitches(
                Silent=installer.silent_switches,
                SilentWithProgress=installer.silent_with_progress_switches
            )

        winget_installer = WinGetInstaller(
            InstallerIdentifier=f"{package.identifier}-{version.version}-{installer.architecture.value}",
            InstallerSha256=installer.sha256,
            InstallerUrl=installer.installer_url,
            Architecture=arch_map.get(installer.architecture.value, "x64"),
            InstallerType=type_map.get(installer.installer_type.value, "exe"),
            Scope=installer.scope.value if installer.scope else None,
            InstallerSwitches=installer_switches,
            ProductCode=installer.product_code,
            MinimumOSVersion=installer.minimum_os_version,
            SignatureSha256=installer.signature_sha256,
            PackageFamilyName=installer.package_family_name
        )
        installers.append(winget_installer)

    # Build manifest
    manifest = WinGetManifest(
        PackageIdentifier=package.identifier,
        PackageVersion=version.version,
        PackageName=package.name,
        Publisher=package.publisher,
        Description=package.description,
        Homepage=package.homepage_url,
        License=package.license,
        LicenseUrl=package.license_url,
        Copyright=package.copyright,
        Tags=package.tags if package.tags else None,
        ReleaseNotes=version.release_notes,
        ReleaseNotesUrl=version.release_notes_url,
        Installers=installers
    )

    return manifest
