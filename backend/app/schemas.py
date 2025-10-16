"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

from app.models import UserRole, InstallerType, Architecture, InstallerScope


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ==================== Auth Schemas ====================

class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: int
    role: str
    exp: int


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ==================== Package Schemas ====================

class PackageBase(BaseModel):
    """Base package schema"""
    identifier: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    publisher: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    license: Optional[str] = None
    license_url: Optional[str] = None
    copyright: Optional[str] = None
    tags: Optional[List[str]] = None


class PackageCreate(PackageBase):
    """Package creation schema"""
    is_mirrored: bool = False


class PackageUpdate(BaseModel):
    """Package update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    publisher: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    license: Optional[str] = None
    license_url: Optional[str] = None
    copyright: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PackageResponse(PackageBase):
    """Package response schema"""
    id: int
    is_active: bool
    is_mirrored: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PackageWithVersions(PackageResponse):
    """Package with versions"""
    versions: List["VersionResponse"] = []

    model_config = {"from_attributes": True}


# ==================== Version Schemas ====================

class VersionBase(BaseModel):
    """Base version schema"""
    version: str = Field(min_length=1, max_length=100)
    release_notes: Optional[str] = None
    release_notes_url: Optional[str] = None
    release_date: Optional[datetime] = None


class VersionCreate(VersionBase):
    """Version creation schema"""
    package_id: int


class VersionUpdate(BaseModel):
    """Version update schema"""
    release_notes: Optional[str] = None
    release_notes_url: Optional[str] = None
    release_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class VersionResponse(VersionBase):
    """Version response schema"""
    id: int
    package_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VersionWithInstallers(VersionResponse):
    """Version with installers"""
    installers: List["InstallerResponse"] = []

    model_config = {"from_attributes": True}


# ==================== Installer Schemas ====================

class InstallerBase(BaseModel):
    """Base installer schema"""
    architecture: Architecture
    installer_type: InstallerType
    scope: Optional[InstallerScope] = None
    silent_switches: Optional[str] = None
    silent_with_progress_switches: Optional[str] = None
    product_code: Optional[str] = None
    minimum_os_version: Optional[str] = None
    signature_sha256: Optional[str] = None
    package_family_name: Optional[str] = None


class InstallerCreate(InstallerBase):
    """Installer creation schema"""
    version_id: int
    s3_key: str
    file_name: str
    content_type: str
    size_bytes: int
    sha256: str
    installer_url: str


class InstallerUpdate(BaseModel):
    """Installer update schema"""
    scope: Optional[InstallerScope] = None
    silent_switches: Optional[str] = None
    silent_with_progress_switches: Optional[str] = None
    product_code: Optional[str] = None
    minimum_os_version: Optional[str] = None
    is_active: Optional[bool] = None


class InstallerResponse(InstallerBase):
    """Installer response schema"""
    id: int
    version_id: int
    s3_key: str
    file_name: str
    content_type: str
    size_bytes: int
    sha256: str
    installer_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==================== WinGet REST API Schemas ====================

class WinGetInformation(BaseModel):
    """WinGet /information endpoint response"""
    Data: Dict[str, Any] = {
        "SourceIdentifier": "Private.WinGet.Source",
        "ServerSupportedVersions": ["1.0.0", "1.1.0", "1.4.0", "1.5.0", "1.6.0", "1.7.0"]
    }


class WinGetInstallerSwitches(BaseModel):
    """WinGet installer switches"""
    Silent: Optional[str] = None
    SilentWithProgress: Optional[str] = None


class WinGetInstaller(BaseModel):
    """WinGet installer object"""
    InstallerIdentifier: Optional[str] = None
    InstallerSha256: str
    InstallerUrl: str
    Architecture: str
    InstallerType: str
    Scope: Optional[str] = None
    InstallerSwitches: Optional[WinGetInstallerSwitches] = None
    ProductCode: Optional[str] = None
    MinimumOSVersion: Optional[str] = None
    SignatureSha256: Optional[str] = None
    PackageFamilyName: Optional[str] = None


class WinGetVersion(BaseModel):
    """WinGet version object"""
    PackageVersion: str
    Channel: Optional[str] = None
    PackageFamilyNames: Optional[List[str]] = None
    ProductCodes: Optional[List[str]] = None


class WinGetManifest(BaseModel):
    """WinGet manifest object"""
    PackageIdentifier: str
    PackageVersion: str
    PackageName: str
    Publisher: str
    Description: Optional[str] = None
    Homepage: Optional[str] = None
    License: Optional[str] = None
    LicenseUrl: Optional[str] = None
    Copyright: Optional[str] = None
    Tags: Optional[List[str]] = None
    ReleaseNotes: Optional[str] = None
    ReleaseNotesUrl: Optional[str] = None
    Installers: List[WinGetInstaller]


class WinGetSearchRequest(BaseModel):
    """WinGet /manifestSearch request"""
    MaximumResults: Optional[int] = 100
    FetchAllManifests: Optional[bool] = False
    Query: Optional[Dict[str, Any]] = None
    Inclusions: Optional[List[Dict[str, Any]]] = None
    Filters: Optional[List[Dict[str, Any]]] = None


class WinGetPackageMatchInfo(BaseModel):
    """WinGet package match info"""
    PackageIdentifier: str
    PackageName: str
    Publisher: str


class WinGetSearchMatch(BaseModel):
    """WinGet search result match"""
    PackageIdentifier: str
    PackageName: str
    Publisher: str
    Versions: List[WinGetVersion]


class WinGetSearchResponse(BaseModel):
    """WinGet /manifestSearch response"""
    Data: List[WinGetSearchMatch]


class WinGetVersionsResponse(BaseModel):
    """WinGet /packageVersions response"""
    Data: List[WinGetVersion]


class WinGetManifestResponse(BaseModel):
    """WinGet /packageManifests response"""
    Data: WinGetManifest


# ==================== Upload Schemas ====================

class UploadInstallerRequest(BaseModel):
    """Upload installer request"""
    version_id: int
    architecture: Architecture
    installer_type: InstallerType
    scope: Optional[InstallerScope] = None
    silent_switches: Optional[str] = None
    silent_with_progress_switches: Optional[str] = None
    product_code: Optional[str] = None


class UploadFromUrlRequest(BaseModel):
    """Upload from URL request"""
    version_id: int
    architecture: Architecture
    installer_type: InstallerType
    scope: Optional[InstallerScope] = None
    source_url: str
    expected_sha256: Optional[str] = None
    silent_switches: Optional[str] = None
    silent_with_progress_switches: Optional[str] = None


# ==================== Audit Log Schemas ====================

class AuditLogResponse(BaseModel):
    """Audit log response"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    id: int
    actor_username: str
    action: str
    entity_type: str
    entity_id: Optional[int]
    entity_identifier: Optional[str]
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias="meta",
        serialization_alias="metadata"
    )
    ip_address: Optional[str]
    timestamp: datetime


# ==================== Statistics Schemas ====================

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_packages: int
    total_versions: int
    total_installers: int
    total_size_bytes: int
    mirrored_packages: int
    manual_packages: int
    recent_updates: int


# ==================== Allow List Schemas ====================

class AllowListEntry(BaseModel):
    """Allow list entry"""
    package_identifier: str
    architectures: Optional[List[str]] = None
    installer_types: Optional[List[str]] = None
    max_versions: Optional[int] = None


class AllowListConfig(BaseModel):
    """Allow list configuration"""
    packages: List[AllowListEntry]


# ==================== Metadata Extraction Schemas ====================

class ExtractedMetadata(BaseModel):
    """Extracted metadata from installer file"""
    product_name: Optional[str] = None
    publisher: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    copyright: Optional[str] = None
    file_description: Optional[str] = None


class ExtractMetadataRequest(BaseModel):
    """Request to extract metadata from URL"""
    url: str


# Update forward references
PackageWithVersions.model_rebuild()
VersionWithInstallers.model_rebuild()
