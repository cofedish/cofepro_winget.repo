"""
WinGet public source interface
Query official Microsoft WinGet repository
"""
import logging
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class WinGetPublicSource:
    """
    Interface to public WinGet REST source
    Uses official Microsoft REST API
    """

    def __init__(self, base_url: str = "https://winget.azureedge.net"):
        """
        Initialize WinGet public source

        Args:
            base_url: Base URL for WinGet REST API
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Private-WinGet-Updater/1.0",
                "Accept": "application/json"
            }
        )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def search_package(self, package_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Search for package by identifier

        Args:
            package_identifier: Package identifier (e.g., "7zip.7zip")

        Returns:
            Package data or None if not found
        """
        try:
            # Use manifestSearch endpoint
            response = await self.client.post(
                f"{self.base_url}/manifestSearch",
                json={
                    "MaximumResults": 1,
                    "Query": {
                        "KeyWord": package_identifier,
                        "MatchType": "Exact"
                    }
                }
            )

            if response.status_code != 200:
                logger.error(f"Failed to search package {package_identifier}: {response.status_code}")
                return None

            data = response.json()
            matches = data.get("Data", [])

            if not matches:
                logger.warning(f"Package {package_identifier} not found in public source")
                return None

            return matches[0]

        except Exception as e:
            logger.error(f"Error searching package {package_identifier}: {e}")
            return None

    async def get_package_versions(self, package_identifier: str) -> List[str]:
        """
        Get all versions for package

        Args:
            package_identifier: Package identifier

        Returns:
            List of version strings
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/packageVersions/{package_identifier}"
            )

            if response.status_code != 200:
                logger.error(f"Failed to get versions for {package_identifier}: {response.status_code}")
                return []

            data = response.json()
            versions = data.get("Data", [])

            return [v["PackageVersion"] for v in versions]

        except Exception as e:
            logger.error(f"Error getting versions for {package_identifier}: {e}")
            return []

    async def get_package_manifest(
        self,
        package_identifier: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get package manifest

        Args:
            package_identifier: Package identifier
            version: Specific version (if None, gets latest)

        Returns:
            Manifest data or None
        """
        try:
            if version:
                url = f"{self.base_url}/packageManifests/{package_identifier}/{version}"
            else:
                url = f"{self.base_url}/packageManifests/{package_identifier}"

            response = await self.client.get(url)

            if response.status_code != 200:
                logger.error(f"Failed to get manifest for {package_identifier}: {response.status_code}")
                return None

            data = response.json()
            return data.get("Data")

        except Exception as e:
            logger.error(f"Error getting manifest for {package_identifier}: {e}")
            return None

    async def get_latest_version(self, package_identifier: str) -> Optional[str]:
        """
        Get latest version for package

        Args:
            package_identifier: Package identifier

        Returns:
            Latest version string or None
        """
        versions = await self.get_package_versions(package_identifier)
        if not versions:
            return None

        # Simple sort (could be improved with semantic versioning)
        sorted_versions = sorted(versions, reverse=True)
        return sorted_versions[0] if sorted_versions else None

    async def download_installer(
        self,
        installer_url: str,
        expected_sha256: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Download installer from URL

        Args:
            installer_url: Installer URL
            expected_sha256: Expected SHA256 hash for verification

        Returns:
            File content as bytes or None
        """
        try:
            logger.info(f"Downloading installer from {installer_url}")

            response = await self.client.get(installer_url)

            if response.status_code != 200:
                logger.error(f"Failed to download installer: {response.status_code}")
                return None

            content = response.content

            # Verify SHA256 if provided
            if expected_sha256:
                import hashlib
                actual_sha256 = hashlib.sha256(content).hexdigest()

                if actual_sha256.lower() != expected_sha256.lower():
                    logger.error(
                        f"SHA256 mismatch! Expected: {expected_sha256}, Got: {actual_sha256}"
                    )
                    return None

                logger.info("SHA256 verification passed")

            return content

        except Exception as e:
            logger.error(f"Error downloading installer: {e}")
            return None

    async def get_filtered_installers(
        self,
        manifest: Dict[str, Any],
        allowed_architectures: List[str],
        allowed_installer_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter installers by architecture and type

        Args:
            manifest: Package manifest
            allowed_architectures: List of allowed architectures
            allowed_installer_types: List of allowed installer types

        Returns:
            Filtered list of installers
        """
        installers = manifest.get("Installers", [])
        filtered = []

        for installer in installers:
            arch = installer.get("Architecture", "").lower()
            installer_type = installer.get("InstallerType", "").lower()

            # Check architecture
            if allowed_architectures and arch not in [a.lower() for a in allowed_architectures]:
                continue

            # Check installer type
            if allowed_installer_types and installer_type not in [t.lower() for t in allowed_installer_types]:
                continue

            filtered.append(installer)

        return filtered
