"""
Utility functions
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User


async def create_audit_log(
    db: AsyncSession,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    entity_identifier: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> None:
    """
    Create audit log entry

    Args:
        db: Database session
        actor: User performing action
        action: Action type (create, update, delete, upload, etc.)
        entity_type: Entity type (package, version, installer, etc.)
        entity_id: Entity ID
        entity_identifier: Entity identifier (for packages)
        meta: Additional metadata
        request: FastAPI request object for IP/user-agent
    """
    ip_address = None
    user_agent = None

    if request:
        # Get real IP from X-Forwarded-For or X-Real-IP headers (behind nginx)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.headers.get("X-Real-IP") or request.client.host

        user_agent = request.headers.get("User-Agent")

    audit_log = AuditLog(
        actor_id=actor.id,
        actor_username=actor.username,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_identifier=entity_identifier,
        meta=meta,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow()
    )

    db.add(audit_log)
    await db.commit()


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Setup application logging

    Args:
        log_level: Logging level
        log_format: Log format (json or text)
    """
    if log_format == "json":
        # JSON logging format
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Standard text format
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = filename.split("/")[-1].split("\\")[-1]

    # Replace unsafe characters
    unsafe_chars = ["<", ">", ":", '"', "|", "?", "*"]
    for char in unsafe_chars:
        filename = filename.replace(char, "_")

    return filename


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human-readable string

    Args:
        bytes_value: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"
