"""
Updater configuration
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Updater settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    base_url: str = Field(..., alias="BASE_URL")

    # Database
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="winget_repo", alias="POSTGRES_DB")
    postgres_user: str = Field(default="winget", alias="POSTGRES_USER")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD")

    # S3/MinIO
    s3_endpoint: str = Field(..., alias="S3_ENDPOINT")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_bucket: str = Field(default="winget-installers", alias="S3_BUCKET")
    s3_access_key: str = Field(..., alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(..., alias="S3_SECRET_KEY")
    s3_secure: bool = Field(default=True, alias="S3_SECURE")
    s3_force_path_style: bool = Field(default=True, alias="S3_FORCE_PATH_STYLE")

    # Updater settings
    allowlist_path: str = Field(default="/app/allow-list.json", alias="ALLOWLIST_PATH")
    updater_interval_minutes: int = Field(default=60, alias="UPDATER_INTERVAL_MINUTES")
    updater_max_versions_per_package: int = Field(default=5, alias="UPDATER_MAX_VERSIONS_PER_PACKAGE")
    updater_architectures: str = Field(default="x64,x86", alias="UPDATER_ARCHITECTURES")
    updater_installer_types: str = Field(default="exe,msi,msix", alias="UPDATER_INSTALLER_TYPES")

    # Service token for API calls
    service_username: str = Field(default="service", alias="SERVICE_USERNAME")
    service_password: str = Field(..., alias="SERVICE_PASSWORD")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def database_url(self) -> str:
        """Generate async database URL"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def updater_architectures_list(self) -> List[str]:
        """Parse updater architectures"""
        return [arch.strip() for arch in self.updater_architectures.split(",")]

    @property
    def updater_installer_types_list(self) -> List[str]:
        """Parse updater installer types"""
        return [itype.strip() for itype in self.updater_installer_types.split(",")]


settings = Settings()
