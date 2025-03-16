from fastapi import HTTPException, status
from rbac_management.crud import get_user_permissions, get_role
from sqlalchemy.orm import Session
from models.user_models import User


def is_admin(user: User, db: Session) -> bool:
    """Check if user has admin role permissions."""
    # First, check if the user has a role
    if not user or not hasattr(user, "role_id") or not user.role_id:
        return False
    
    # Check the role name directly
    role = get_role(db, user.role_id)
    if role and role.name.lower() in ["admin", "superadmin"]:
        return True
    
    # Check for specific admin permission as a fallback
    permissions = get_user_permissions(db, user.id)
    print("permissions", permissions)
    return any(
        hasattr(p, "action") and hasattr(p, "resource") and
        p.action == "admin" and p.resource == "all" 
        for p in permissions
    )


def check_user_access(requesting_user: User, target_user_id: int, db: Session):
    """Allow access if user is viewing their own profile or has admin permissions"""
    if requesting_user.id == target_user_id:
        return True
    
    if not is_admin(requesting_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this profile"
        )