"""
File upload and download routes
"""
import io
import tempfile
import os
from typing import Optional
from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile,
    File, Request
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import httpx

from app.database import get_db
from app.models import User, UserRole, Version, Installer
from app.schemas import InstallerResponse, UploadFromUrlRequest, ExtractedMetadata, ExtractMetadataRequest
from app.security import require_role
from app.s3 import s3_client, calculate_sha256, generate_s3_key
from app.utils import create_audit_log, sanitize_filename
from app.config import settings
from app.metadata_extractor import extract_metadata, extract_metadata_from_url

router = APIRouter(tags=["Upload & Download"])


@router.post("/admin/upload", response_model=InstallerResponse)
async def upload_installer(
    version_id: int,
    architecture: str,
    installer_type: str,
    file: UploadFile = File(...),
    scope: Optional[str] = None,
    silent_switches: Optional[str] = None,
    silent_with_progress_switches: Optional[str] = None,
    product_code: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Upload installer file for a version
    """
    # Get version with package
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

    package = version.package

    # Sanitize filename
    filename = sanitize_filename(file.filename)

    # Generate S3 key
    s3_key = generate_s3_key(
        package.identifier,
        version.version,
        architecture,
        filename
    )

    # Read file content
    file_content = await file.read()
    file_obj = io.BytesIO(file_content)

    # Calculate SHA256
    sha256 = calculate_sha256(file_obj)

    # Upload to S3
    try:
        _, size_bytes = s3_client.upload_file(
            file_obj,
            s3_key,
            file.content_type or "application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}"
        )

    # Generate installer URL
    installer_url = f"{settings.base_url}/dl/{s3_key}"

    # Create installer record
    from app.models import Architecture, InstallerType, InstallerScope

    installer = Installer(
        version_id=version_id,
        architecture=Architecture(architecture),
        installer_type=InstallerType(installer_type),
        scope=InstallerScope(scope) if scope else None,
        s3_key=s3_key,
        file_name=filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        sha256=sha256,
        installer_url=installer_url,
        silent_switches=silent_switches,
        silent_with_progress_switches=silent_with_progress_switches,
        product_code=product_code
    )

    db.add(installer)
    await db.commit()
    await db.refresh(installer)

    # Audit log
    await create_audit_log(
        db, current_user, "upload", "installer",
        entity_id=installer.id,
        entity_identifier=package.identifier,
        meta={
            "version": version.version,
            "filename": filename,
            "size": size_bytes,
            "sha256": sha256
        },
        request=request
    )

    return installer


@router.post("/admin/upload-from-url", response_model=InstallerResponse)
async def upload_installer_from_url(
    upload_data: UploadFromUrlRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Upload installer from URL
    """
    # Get version with package
    result = await db.execute(
        select(Version)
        .where(Version.id == upload_data.version_id)
        .options(selectinload(Version.package))
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )

    package = version.package

    # Download file from URL
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
            response = await client.get(upload_data.source_url)
            response.raise_for_status()
            file_content = response.content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download file from URL: {str(e)}"
        )

    # Create file object
    file_obj = io.BytesIO(file_content)

    # Calculate SHA256
    sha256 = calculate_sha256(file_obj)

    # Verify SHA256 if provided
    if upload_data.expected_sha256:
        if sha256.lower() != upload_data.expected_sha256.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SHA256 mismatch. Expected: {upload_data.expected_sha256}, Got: {sha256}"
            )

    # Extract filename from URL
    filename = upload_data.source_url.split("/")[-1].split("?")[0]
    filename = sanitize_filename(filename)

    if not filename:
        filename = f"installer.{upload_data.installer_type.value}"

    # Generate S3 key
    s3_key = generate_s3_key(
        package.identifier,
        version.version,
        upload_data.architecture.value,
        filename
    )

    # Determine content type
    content_type = "application/octet-stream"
    if upload_data.installer_type.value == "msi":
        content_type = "application/x-msi"
    elif upload_data.installer_type.value in ["exe", "inno", "nullsoft", "burn"]:
        content_type = "application/x-msdownload"
    elif upload_data.installer_type.value in ["msix", "appx"]:
        content_type = "application/vnd.ms-appx"

    # Upload to S3
    try:
        _, size_bytes = s3_client.upload_file(file_obj, s3_key, content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}"
        )

    # Generate installer URL
    installer_url = f"{settings.base_url}/dl/{s3_key}"

    # Create installer record
    installer = Installer(
        version_id=upload_data.version_id,
        architecture=upload_data.architecture,
        installer_type=upload_data.installer_type,
        scope=upload_data.scope,
        s3_key=s3_key,
        file_name=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        installer_url=installer_url,
        silent_switches=upload_data.silent_switches,
        silent_with_progress_switches=upload_data.silent_with_progress_switches
    )

    db.add(installer)
    await db.commit()
    await db.refresh(installer)

    # Audit log
    await create_audit_log(
        db, current_user, "upload", "installer",
        entity_id=installer.id,
        entity_identifier=package.identifier,
        meta={
            "version": version.version,
            "source_url": upload_data.source_url,
            "filename": filename,
            "size": size_bytes,
            "sha256": sha256
        },
        request=request
    )

    return installer


@router.get("/dl/{s3_key:path}")
async def download_installer(
    s3_key: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download installer file
    Streams file from S3 to client
    Supports HTTP Range requests
    """
    # Verify installer exists in database
    result = await db.execute(
        select(Installer).where(Installer.s3_key == s3_key)
    )
    installer = result.scalar_one_or_none()

    if not installer or not installer.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installer not found"
        )

    # Check if file exists in S3
    if not s3_client.file_exists(s3_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installer file not found in storage"
        )

    # Get file metadata
    try:
        metadata = s3_client.get_file_metadata(s3_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file metadata: {str(e)}"
        )

    # Stream file from S3
    try:
        stream = s3_client.stream_file(s3_key)

        # Create streaming response
        def iterfile():
            for chunk in stream.iter_chunks(chunk_size=8192):
                yield chunk

        headers = {
            "Content-Disposition": f'attachment; filename="{installer.file_name}"',
            "Content-Length": str(metadata['content_length']),
            "Accept-Ranges": "bytes"
        }

        return StreamingResponse(
            iterfile(),
            media_type=installer.content_type,
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream file: {str(e)}"
        )


@router.post("/admin/extract-metadata", response_model=ExtractedMetadata)
async def extract_metadata_from_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Extract metadata from uploaded installer file (MSI or EXE)

    This endpoint extracts product name, publisher, version, and description
    from the installer file's embedded metadata
    """
    # Save file to temp location
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])

    try:
        # Write uploaded file to temp
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        temp_file.close()

        # Extract metadata
        metadata = extract_metadata(temp_file.name)

        # Cleanup
        os.unlink(temp_file.name)

        # Convert to response model
        return ExtractedMetadata(
            product_name=metadata.product_name,
            publisher=metadata.publisher,
            version=metadata.version,
            description=metadata.description,
            copyright=metadata.copyright,
            file_description=metadata.file_description
        )
    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract metadata: {str(e)}"
        )


@router.post("/admin/extract-metadata-from-url", response_model=ExtractedMetadata)
async def extract_metadata_from_url_endpoint(
    request_data: ExtractMetadataRequest,
    current_user: User = Depends(require_role(UserRole.MAINTAINER))
):
    """
    Extract metadata from installer file at URL (MSI or EXE)

    Downloads the file (or first part) and extracts metadata
    """
    try:
        metadata = await extract_metadata_from_url(request_data.url)

        return ExtractedMetadata(
            product_name=metadata.product_name,
            publisher=metadata.publisher,
            version=metadata.version,
            description=metadata.description,
            copyright=metadata.copyright,
            file_description=metadata.file_description
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract metadata from URL: {str(e)}"
        )
