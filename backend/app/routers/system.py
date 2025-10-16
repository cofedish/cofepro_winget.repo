"""
System management routes - allow list, updater control
"""
import json
import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.models import User, UserRole
from app.security import require_role

router = APIRouter(prefix="/system", tags=["System"])


class AllowListModel(BaseModel):
    content: str  # JSON content as string


@router.get("/allow-list")
async def get_allow_list(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Get current allow list configuration
    """
    allow_list_path = "/app/allow-list.json"

    if not os.path.exists(allow_list_path):
        # Return default structure
        return {
            "content": json.dumps({
                "packages": []
            }, indent=2)
        }

    with open(allow_list_path, 'r') as f:
        content = f.read()

    return {"content": content}


@router.post("/allow-list")
async def update_allow_list(
    data: AllowListModel,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Update allow list configuration
    """
    # Validate JSON
    try:
        parsed = json.loads(data.content)
        if "packages" not in parsed:
            raise ValueError("Missing 'packages' key")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}"
        )

    # Write to file
    allow_list_path = "/app/allow-list.json"
    with open(allow_list_path, 'w') as f:
        f.write(data.content)

    return {"message": "Allow list updated successfully"}


@router.post("/updater/trigger")
async def trigger_updater(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Trigger updater synchronization
    Note: This sends a signal to the updater to reload allow-list
    """
    import subprocess
    import os

    try:
        # Check if running in production (remote server)
        ssh_host = os.getenv("SSH_HOST")
        ssh_password = os.getenv("SSH_PASSWORD")
        deploy_path = os.getenv("DEPLOY_PATH", "/root/winget-repo/deploy")

        if ssh_host and ssh_password:
            # Production: SSH to host and restart updater
            cmd = [
                "sshpass", "-p", ssh_password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"root@{ssh_host}",
                f"cd {deploy_path} && docker compose restart updater"
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return {"message": "Updater container restarted successfully via SSH"}
        else:
            # Local development: Send signal to updater container
            # The updater will automatically sync on next cycle (every 60min by default)
            return {
                "message": "Updater will sync on next cycle. For immediate sync, restart the updater container manually: docker compose restart updater"
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger updater: {str(e)}"
        )
