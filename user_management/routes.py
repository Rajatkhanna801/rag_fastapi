# user_management/routs.py
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import Any
from database import get_db
from models.user_models import User
from user_management.schema import UserResponse, UserUpdate
from user_management.main import get_user_by_id, update_user_profile, soft_delete_user
from rbac_management.dependencies import authorize
from auth.main import get_current_active_user  # Use this instead of authorize
from common import check_user_access, is_admin
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import Any


router = APIRouter(prefix="/users", tags=["users"])
        
        
@router.get("/{user_id}", response_model=UserResponse)
def get_user_profile(
    user_id: int = Path(..., title="The ID of the user to get"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get user profile by ID. User can only access their own profile or admin can access any."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Check if the current user has permission to view this profile
    check_user_access(current_user, user_id, db)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user_profile_by_id(
    *,
    user_id: int = Path(..., title="The ID of the user to update"),
    db: Session = Depends(get_db),
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update user profile by ID. Requires update user permission or to be the owner of the profile."""
    # Check if the user exists
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Check if the current user has permission to update this profile
    check_user_access(current_user, user_id, db)
    # Update the user profile
    updated_user = update_user_profile(db, user_id, user_data)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user_profile_by_id(
    *,
    user_id: int = Path(..., title="The ID of the user to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Soft delete user profile by ID. User can only delete their own profile or admin can delete any."""
    # Check if the user exists
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Check if the current user has permission to delete this profile
    check_user_access(current_user, user_id, db)
    # Check if user is already deleted
    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already deleted",
        )
    # Soft delete the user
    soft_delete_user(db, user_id)
    return {"message": "User deleted successfully"}


# Route to get all users (admin only)
@router.get("/", response_model=list[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # Use get_current_active_user instead
) -> Any:
    """Get all users. Admin only."""
    # Manual check for admin permissions
    if not is_admin(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to list all users"
        )
    users = db.query(User).offset(skip).limit(limit).all()
    return users