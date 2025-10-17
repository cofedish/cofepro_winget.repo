"""
Updater main service
Automatically mirrors packages from public WinGet to private repository
"""
import asyncio
import json
import logging
import sys
import hashlib
import io
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
import boto3
from botocore.client import Config

from config import settings
from winget_source import WinGetPublicSource

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class S3Client:
    """S3/MinIO client"""

    def __init__(self):
        """Initialize S3 client"""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path' if settings.s3_force_path_style else 'auto'}
            ),
            use_ssl=settings.s3_secure
        )
        self.bucket = settings.s3_bucket

    def upload_file(self, file_content: bytes, s3_key: str, content_type: str = "application/octet-stream") -> int:
        """Upload file to S3"""
        try:
            sha256_hash = hashlib.sha256(file_content).hexdigest()

            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'sha256': sha256_hash,
                    'original-size': str(len(file_content))
                }
            )
            return len(file_content)
        except Exception as e:
            raise Exception(f"Failed to upload to S3: {e}")

    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except:
            return False


class PackageUpdater:
    """Package updater service"""

    def __init__(self):
        """Initialize updater"""
        self.winget_source = WinGetPublicSource()
        self.s3_client = S3Client()
        self.http_client = httpx.AsyncClient(timeout=300.0, follow_redirects=True)

        # Initialize database
        engine = create_async_engine(settings.database_url, echo=False)
        self.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

        # API credentials
        self.api_token = None

    async def close(self):
        """Close connections"""
        await self.winget_source.close()
        await self.http_client.aclose()

    async def authenticate(self) -> bool:
        """
        Authenticate with backend API
        """
        try:
            response = await self.http_client.post(
                f"{settings.base_url}/api/auth/login",
                json={
                    "username": settings.service_username,
                    "password": settings.service_password
                }
            )

            if response.status_code != 200:
                logger.error(f"Authentication failed: {response.status_code}")
                return False

            data = response.json()
            self.api_token = data["access_token"]
            logger.info("Successfully authenticated with backend API")
            return True

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def load_auto_update_configs(self) -> List[Dict[str, Any]]:
        """
        Load auto-update configurations via API

        Returns:
            List of package configurations
        """
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}

            # Get all enabled auto-update configs
            response = await self.http_client.get(
                f"{settings.base_url}/api/admin/auto-update/configs?enabled_only=true",
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"Failed to load auto-update configs: {response.status_code}")
                return []

            packages_data = response.json()

            packages = []
            for pkg in packages_data:
                if not pkg.get("auto_update_config"):
                    continue

                config = pkg["auto_update_config"]
                packages.append({
                    "package_identifier": pkg["identifier"],
                    "architectures": config.get("architectures") or settings.updater_architectures_list,
                    "installer_types": config.get("installer_types") or settings.updater_installer_types_list,
                    "max_versions": config.get("max_versions", settings.updater_max_versions_per_package)
                })

            logger.info(f"Loaded {len(packages)} packages from API")
            return packages

        except Exception as e:
            logger.error(f"Failed to load auto-update configs: {e}")
            logger.exception(e)
            return []

    async def check_package_exists(self, package_identifier: str) -> Optional[int]:
        """
        Check if package exists in database

        Returns:
            Package ID if exists, None otherwise
        """
        try:
            async with self.SessionLocal() as session:
                # Import models here to avoid circular imports
                sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
                from app.models import Package

                result = await session.execute(
                    select(Package).where(Package.identifier == package_identifier)
                )
                package = result.scalar_one_or_none()
                return package.id if package else None

        except Exception as e:
            logger.error(f"Error checking package existence: {e}")
            return None

    async def create_package_via_api(self, manifest: Dict[str, Any]) -> Optional[int]:
        """
        Create package via API

        Returns:
            Package ID if created, None otherwise
        """
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}

            package_data = {
                "identifier": manifest["PackageIdentifier"],
                "name": manifest["PackageName"],
                "publisher": manifest["Publisher"],
                "description": manifest.get("Description"),
                "homepage_url": manifest.get("Homepage"),
                "license": manifest.get("License"),
                "license_url": manifest.get("LicenseUrl"),
                "copyright": manifest.get("Copyright"),
                "tags": manifest.get("Tags"),
                "is_mirrored": True
            }

            response = await self.http_client.post(
                f"{settings.base_url}/api/admin/packages",
                json=package_data,
                headers=headers
            )

            if response.status_code == 201:
                data = response.json()
                logger.info(f"Created package: {manifest['PackageIdentifier']}")
                return data["id"]
            elif response.status_code == 409:
                # Package already exists, get it
                package_id = await self.check_package_exists(manifest["PackageIdentifier"])
                return package_id
            else:
                logger.error(f"Failed to create package: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating package: {e}")
            return None

    async def check_version_exists(self, package_id: int, version: str) -> Optional[int]:
        """
        Check if version exists

        Returns:
            Version ID if exists, None otherwise
        """
        try:
            async with self.SessionLocal() as session:
                sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
                from app.models import Version

                result = await session.execute(
                    select(Version).where(
                        Version.package_id == package_id,
                        Version.version == version
                    )
                )
                version_obj = result.scalar_one_or_none()
                return version_obj.id if version_obj else None

        except Exception as e:
            logger.error(f"Error checking version existence: {e}")
            return None

    async def create_version_via_api(
        self,
        package_id: int,
        manifest: Dict[str, Any]
    ) -> Optional[int]:
        """
        Create version via API

        Returns:
            Version ID if created, None otherwise
        """
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}

            version_data = {
                "package_id": package_id,
                "version": manifest["PackageVersion"],
                "release_notes": manifest.get("ReleaseNotes"),
                "release_notes_url": manifest.get("ReleaseNotesUrl")
            }

            response = await self.http_client.post(
                f"{settings.base_url}/api/admin/versions",
                json=version_data,
                headers=headers
            )

            if response.status_code == 201:
                data = response.json()
                logger.info(f"Created version: {manifest['PackageVersion']}")
                return data["id"]
            elif response.status_code == 409:
                # Version already exists
                version_id = await self.check_version_exists(package_id, manifest["PackageVersion"])
                return version_id
            else:
                logger.error(f"Failed to create version: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating version: {e}")
            return None

    def generate_s3_key(
        self,
        package_identifier: str,
        version: str,
        architecture: str,
        filename: str
    ) -> str:
        """Generate S3 object key"""
        safe_identifier = package_identifier.replace("/", "_").replace("\\", "_")
        safe_version = version.replace("/", "_").replace("\\", "_")
        safe_arch = architecture.replace("/", "_").replace("\\", "_")
        return f"{safe_identifier}/{safe_version}/{safe_arch}/{filename}"

    async def upload_installer_via_api(
        self,
        version_id: int,
        installer_data: Dict[str, Any],
        file_content: bytes,
        s3_key: str
    ) -> bool:
        """
        Upload installer via API

        Returns:
            True if successful, False otherwise
        """
        try:
            # First upload to S3
            content_type = "application/octet-stream"
            installer_type = installer_data.get("InstallerType", "").lower()

            if installer_type == "msi":
                content_type = "application/x-msi"
            elif installer_type in ["exe", "inno", "nullsoft", "burn"]:
                content_type = "application/x-msdownload"
            elif installer_type in ["msix", "appx"]:
                content_type = "application/vnd.ms-appx"

            # Check if already uploaded
            if self.s3_client.file_exists(s3_key):
                logger.info(f"Installer already exists in S3: {s3_key}")
            else:
                size = self.s3_client.upload_file(file_content, s3_key, content_type)
                logger.info(f"Uploaded installer to S3: {s3_key} ({size} bytes)")

            # Create installer record via API
            headers = {"Authorization": f"Bearer {self.api_token}"}

            # Extract filename from s3_key
            filename = s3_key.split("/")[-1]

            installer_url = f"{settings.base_url}/dl/{s3_key}"

            installer_payload = {
                "version_id": version_id,
                "architecture": installer_data.get("Architecture", "x64").lower(),
                "installer_type": installer_type,
                "scope": installer_data.get("Scope", "").lower() if installer_data.get("Scope") else None,
                "s3_key": s3_key,
                "file_name": filename,
                "content_type": content_type,
                "size_bytes": len(file_content),
                "sha256": installer_data.get("InstallerSha256"),
                "installer_url": installer_url,
                "silent_switches": installer_data.get("InstallerSwitches", {}).get("Silent"),
                "silent_with_progress_switches": installer_data.get("InstallerSwitches", {}).get("SilentWithProgress"),
                "product_code": installer_data.get("ProductCode")
            }

            # Check if installer already exists (by sha256)
            async with self.SessionLocal() as session:
                sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
                from app.models import Installer

                result = await session.execute(
                    select(Installer).where(
                        Installer.version_id == version_id,
                        Installer.sha256 == installer_data.get("InstallerSha256")
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    logger.info(f"Installer already exists in database")
                    return True

            # Create via direct database insert (API endpoint doesn't support this)
            async with self.SessionLocal() as session:
                sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
                from app.models import Installer, Architecture, InstallerType, InstallerScope

                installer = Installer(
                    version_id=version_id,
                    architecture=Architecture(installer_payload["architecture"]),
                    installer_type=InstallerType(installer_payload["installer_type"]),
                    scope=InstallerScope(installer_payload["scope"]) if installer_payload["scope"] else None,
                    s3_key=installer_payload["s3_key"],
                    file_name=installer_payload["file_name"],
                    content_type=installer_payload["content_type"],
                    size_bytes=installer_payload["size_bytes"],
                    sha256=installer_payload["sha256"],
                    installer_url=installer_payload["installer_url"],
                    silent_switches=installer_payload["silent_switches"],
                    silent_with_progress_switches=installer_payload["silent_with_progress_switches"],
                    product_code=installer_payload["product_code"]
                )

                session.add(installer)
                await session.commit()
                logger.info(f"Created installer record in database")

            return True

        except Exception as e:
            logger.error(f"Error uploading installer: {e}")
            return False

    async def sync_package(
        self,
        package_config: Dict[str, Any]
    ) -> bool:
        """
        Sync single package

        Args:
            package_config: Package configuration from allow list

        Returns:
            True if successful, False otherwise
        """
        package_identifier = package_config.get("package_identifier")
        if not package_identifier:
            logger.error("Missing package_identifier in config")
            return False

        logger.info(f"Syncing package: {package_identifier}")

        # Get latest version from public source
        latest_version = await self.winget_source.get_latest_version(package_identifier)
        if not latest_version:
            logger.error(f"Could not get latest version for {package_identifier}")
            return False

        logger.info(f"Latest version: {latest_version}")

        # Get manifest
        manifest = await self.winget_source.get_package_manifest(package_identifier, latest_version)
        if not manifest:
            logger.error(f"Could not get manifest for {package_identifier}")
            return False

        # Check if package exists, create if not
        package_id = await self.check_package_exists(package_identifier)
        if not package_id:
            package_id = await self.create_package_via_api(manifest)
            if not package_id:
                logger.error(f"Failed to create package {package_identifier}")
                return False

        # Check if version exists, create if not
        version_id = await self.check_version_exists(package_id, latest_version)
        if not version_id:
            version_id = await self.create_version_via_api(package_id, manifest)
            if not version_id:
                logger.error(f"Failed to create version {latest_version}")
                return False

        # Filter installers
        allowed_archs = package_config.get("architectures") or settings.updater_architectures_list
        allowed_types = package_config.get("installer_types") or settings.updater_installer_types_list

        installers = await self.winget_source.get_filtered_installers(
            manifest,
            allowed_archs,
            allowed_types
        )

        if not installers:
            logger.warning(f"No installers matching filters for {package_identifier}")
            return True  # Not an error

        logger.info(f"Found {len(installers)} matching installers")

        # Process each installer
        for installer in installers:
            try:
                installer_url = installer.get("InstallerUrl")
                expected_sha256 = installer.get("InstallerSha256")

                if not installer_url or not expected_sha256:
                    logger.warning("Installer missing URL or SHA256, skipping")
                    continue

                logger.info(f"Processing installer: {installer_url}")

                # Download installer
                file_content = await self.winget_source.download_installer(
                    installer_url,
                    expected_sha256
                )

                if not file_content:
                    logger.error("Failed to download installer")
                    continue

                # Generate S3 key
                filename = installer_url.split("/")[-1].split("?")[0]
                if not filename or "." not in filename:
                    filename = f"installer.{installer.get('InstallerType', 'exe').lower()}"

                s3_key = self.generate_s3_key(
                    package_identifier,
                    latest_version,
                    installer.get("Architecture", "x64"),
                    filename
                )

                # Upload installer
                success = await self.upload_installer_via_api(
                    version_id,
                    installer,
                    file_content,
                    s3_key
                )

                if success:
                    logger.info(f"Successfully synced installer")
                else:
                    logger.error(f"Failed to sync installer")

            except Exception as e:
                logger.error(f"Error processing installer: {e}")
                continue

        logger.info(f"Successfully synced package: {package_identifier}")
        return True

    async def run_sync_cycle(self):
        """Run one sync cycle"""
        logger.info("=" * 60)
        logger.info("Starting sync cycle")
        logger.info("=" * 60)

        # Authenticate
        if not await self.authenticate():
            logger.error("Authentication failed, skipping sync cycle")
            return

        # Load auto-update configs from database
        packages = await self.load_auto_update_configs()
        if not packages:
            logger.warning("No packages configured for auto-update")
            return

        logger.info(f"Processing {len(packages)} packages")

        # Sync each package
        success_count = 0
        fail_count = 0

        for package_config in packages:
            try:
                success = await self.sync_package(package_config)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"Error syncing package: {e}")
                fail_count += 1

            # Small delay between packages
            await asyncio.sleep(2)

        logger.info("=" * 60)
        logger.info(f"Sync cycle complete. Success: {success_count}, Failed: {fail_count}")
        logger.info("=" * 60)

    async def run_periodic(self):
        """Run periodic sync"""
        logger.info(f"Updater service started. Interval: {settings.updater_interval_minutes} minutes")

        while True:
            try:
                await self.run_sync_cycle()
            except Exception as e:
                logger.error(f"Error in sync cycle: {e}")

            # Wait for next cycle
            wait_seconds = settings.updater_interval_minutes * 60
            logger.info(f"Waiting {settings.updater_interval_minutes} minutes until next sync...")
            await asyncio.sleep(wait_seconds)


async def main():
    """Main entry point"""
    updater = PackageUpdater()

    try:
        # Run initial sync immediately
        await updater.run_sync_cycle()

        # Then start periodic sync
        await updater.run_periodic()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await updater.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Updater service stopped")
        sys.exit(0)
