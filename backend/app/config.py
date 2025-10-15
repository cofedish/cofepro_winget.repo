"""
Configuration management using pydantic-settings
"""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="Private WinGet Repository", alias="APP_NAME")
    base_url: str = Field(default="http://localhost", alias="BASE_URL")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="production", alias="ENVIRONMENT")

    # Security
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

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

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_search_per_minute: int = Field(default=30, alias="RATE_LIMIT_SEARCH_PER_MINUTE")

    # CORS
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    # Updater
    allowlist_path: str = Field(default="/app/allow-list.json", alias="ALLOWLIST_PATH")
    updater_interval_minutes: int = Field(default=60, alias="UPDATER_INTERVAL_MINUTES")
    updater_max_versions_per_package: int = Field(default=5, alias="UPDATER_MAX_VERSIONS_PER_PACKAGE")
    updater_architectures: str = Field(default="x64,x86", alias="UPDATER_ARCHITECTURES")
    updater_installer_types: str = Field(default="exe,msi,msix", alias="UPDATER_INSTALLER_TYPES")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    @property
    def database_url(self) -> str:
        """Generate async database URL"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Generate sync database URL for Alembic"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def updater_architectures_list(self) -> List[str]:
        """Parse updater architectures"""
        return [arch.strip() for arch in self.updater_architectures.split(",")]

    @property
    def updater_installer_types_list(self) -> List[str]:
        """Parse updater installer types"""
        return [itype.strip() for itype in self.updater_installer_types.split(",")]

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is strong enough"""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v


# Global settings instance
settings = Settings()
