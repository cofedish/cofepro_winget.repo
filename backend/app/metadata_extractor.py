"""
Extract metadata from installer files (MSI, EXE)
"""
import os
import struct
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile

logger = logging.getLogger(__name__)


class InstallerMetadata:
    """Metadata extracted from installer file"""

    def __init__(self):
        self.product_name: Optional[str] = None
        self.publisher: Optional[str] = None
        self.version: Optional[str] = None
        self.description: Optional[str] = None
        self.copyright: Optional[str] = None
        self.file_description: Optional[str] = None


def extract_metadata(file_path: str) -> InstallerMetadata:
    """
    Extract metadata from installer file

    Args:
        file_path: Path to installer file (MSI or EXE)

    Returns:
        InstallerMetadata object with extracted data
    """
    metadata = InstallerMetadata()

    file_ext = Path(file_path).suffix.lower()

    try:
        if file_ext == '.msi':
            return extract_msi_metadata(file_path)
        elif file_ext == '.exe':
            return extract_exe_metadata(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return metadata
    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}")
        return metadata


def extract_msi_metadata(file_path: str) -> InstallerMetadata:
    """Extract metadata from MSI file using olefile"""
    metadata = InstallerMetadata()

    try:
        import olefile

        if not olefile.isOleFile(file_path):
            logger.warning(f"Not a valid MSI file: {file_path}")
            return metadata

        ole = olefile.OleFileIO(file_path)

        # Try to read summary information
        try:
            if ole.exists('\x05SummaryInformation'):
                summary_stream = ole.openstream('\x05SummaryInformation')
                # This is a complex binary format, we'll use basic parsing

                # Read property set header
                summary_data = summary_stream.read()

                # Parse property IDs (simplified)
                # Title (2), Subject (3), Author (4), Keywords (5), Comments (6)
                props = _parse_msi_summary(summary_data)

                metadata.product_name = props.get('title') or props.get('subject')
                metadata.publisher = props.get('author')
                metadata.description = props.get('comments')

        except Exception as e:
            logger.debug(f"Could not read summary info: {e}")

        ole.close()

    except ImportError:
        logger.error("olefile not installed, cannot extract MSI metadata")
    except Exception as e:
        logger.error(f"Error extracting MSI metadata: {e}")

    return metadata


def _parse_msi_summary(data: bytes) -> Dict[str, str]:
    """Parse MSI summary information stream (simplified)"""
    props = {}

    try:
        # Skip header (48 bytes)
        offset = 48

        # This is a very simplified parser
        # Real MSI parsing requires handling the property set structure
        # For production, consider using python-msi or similar library

        # Try to find common strings
        data_str = data.decode('utf-16-le', errors='ignore')

        # Look for patterns (very basic heuristic)
        lines = data_str.split('\x00')
        lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 2]

        # Heuristic: first non-empty strings might be metadata
        if len(lines) > 0:
            props['title'] = lines[0]
        if len(lines) > 1:
            props['author'] = lines[1]
        if len(lines) > 2:
            props['comments'] = lines[2]

    except Exception as e:
        logger.debug(f"MSI summary parsing error: {e}")

    return props


def extract_exe_metadata(file_path: str) -> InstallerMetadata:
    """Extract metadata from EXE file using pefile"""
    metadata = InstallerMetadata()

    try:
        import pefile

        pe = pefile.PE(file_path)

        # Check if file has version information
        if hasattr(pe, 'VS_VERSIONINFO') and pe.VS_VERSIONINFO:
            # Iterate through version info structures
            for vs_struct in pe.VS_VERSIONINFO:
                # Check for StringFileInfo
                if hasattr(vs_struct, 'StringFileInfo') and vs_struct.StringFileInfo:
                    for string_table in vs_struct.StringFileInfo:
                        # Check for StringTable
                        if hasattr(string_table, 'StringTable'):
                            for st in string_table.StringTable:
                                # Get entries dictionary
                                if hasattr(st, 'entries'):
                                    entries = st.entries

                                    # Extract metadata
                                    if b'ProductName' in entries:
                                        metadata.product_name = entries[b'ProductName'].decode('utf-8', errors='ignore')
                                    if b'CompanyName' in entries:
                                        metadata.publisher = entries[b'CompanyName'].decode('utf-8', errors='ignore')
                                    if b'ProductVersion' in entries:
                                        metadata.version = entries[b'ProductVersion'].decode('utf-8', errors='ignore')
                                    if b'FileDescription' in entries:
                                        metadata.file_description = entries[b'FileDescription'].decode('utf-8', errors='ignore')
                                    if b'LegalCopyright' in entries:
                                        metadata.copyright = entries[b'LegalCopyright'].decode('utf-8', errors='ignore')
                                    if b'Comments' in entries:
                                        metadata.description = entries[b'Comments'].decode('utf-8', errors='ignore')
                                    if b'FileVersion' in entries and not metadata.version:
                                        metadata.version = entries[b'FileVersion'].decode('utf-8', errors='ignore')

        # If no description but have file_description, use it
        if not metadata.description and metadata.file_description:
            metadata.description = metadata.file_description

        # If version has extra characters, clean it
        if metadata.version:
            metadata.version = _clean_version(metadata.version)

        pe.close()

    except ImportError:
        logger.error("pefile not installed, cannot extract EXE metadata")
    except Exception as e:
        logger.error(f"Error extracting EXE metadata: {e}", exc_info=True)

    return metadata


def _clean_version(version: str) -> str:
    """Clean version string to standard format"""
    # Remove common prefixes
    version = version.strip()
    if version.lower().startswith('v'):
        version = version[1:]

    # Split by comma or space and take first part
    version = version.replace(',', '.').split()[0]

    # Keep only digits and dots
    parts = []
    for char in version:
        if char.isdigit() or char == '.':
            parts.append(char)

    cleaned = ''.join(parts)

    # Remove leading/trailing dots
    cleaned = cleaned.strip('.')

    # Remove duplicate dots
    while '..' in cleaned:
        cleaned = cleaned.replace('..', '.')

    return cleaned


async def extract_metadata_from_url(url: str) -> InstallerMetadata:
    """
    Download file from URL to temp location and extract metadata

    Args:
        url: URL to installer file

    Returns:
        InstallerMetadata object
    """
    import httpx

    metadata = InstallerMetadata()

    try:
        # Determine file extension from URL
        file_ext = Path(url).suffix.lower()
        if file_ext not in ['.msi', '.exe', '.msix']:
            logger.warning(f"Cannot extract metadata from URL with extension: {file_ext}")
            return metadata

        # Download file to temp location (only first few MB needed for metadata)
        # For large files, we only need the PE header and version resource
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # For EXE, we can try to download only first part (headers usually in first 1-2 MB)
            # For MSI, we need more of the file

            if file_ext == '.exe':
                # Request first 5MB for EXE (version info can be anywhere)
                headers = {'Range': 'bytes=0-5242879'}
                try:
                    response = await client.get(url, headers=headers)
                except:
                    # If range not supported, download full file
                    response = await client.get(url)
            else:
                # For MSI, download more (or full file if small)
                # Try to get first 10MB
                headers = {'Range': 'bytes=0-10485759'}
                try:
                    response = await client.get(url, headers=headers)
                except:
                    # If range not supported, download full file
                    response = await client.get(url)

            if response.status_code in [200, 206]:  # 200 OK or 206 Partial Content
                temp_file.write(response.content)
                temp_file.flush()
                temp_file.close()

                # Extract metadata
                metadata = extract_metadata(temp_file.name)

                # Cleanup
                os.unlink(temp_file.name)
            else:
                logger.warning(f"Failed to download file for metadata extraction: {response.status_code}")
                temp_file.close()
                os.unlink(temp_file.name)

    except Exception as e:
        logger.error(f"Error extracting metadata from URL: {e}", exc_info=True)

    return metadata
