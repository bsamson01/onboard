from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_async_db
from app.models.user import User
from app.core.auth import require_admin

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Get list of users (admin only)."""
    # TODO: Implement user list with proper permissions
    return []


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Get user by ID (admin only)."""
    # TODO: Implement get user by ID
    return {}


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Update user information (admin only)."""
    # TODO: Implement user update
    return {}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete user (admin only)."""
    # TODO: Implement user deletion
    return {"message": "User deleted successfully"}