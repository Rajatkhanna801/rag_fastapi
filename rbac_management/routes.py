from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.user_models import User
from auth.main import get_current_active_user
from rbac_management.schemas import (
    Role, RoleCreate, RoleUpdate,
    Permission, PermissionCreate,
    UserRoleAssign
)
from rbac_management.crud import (
    get_role, get_roles, create_role, update_role, delete_role,
    get_permissions, create_permission, delete_permission,
    assign_role_to_user, get_user_permissions, get_permission_by_details,
    get_role_by_name,
)
from rbac_management.dependencies import authorize

router = APIRouter(prefix="/rbac", tags=["Roles and Permissions"])


# Role endpoints
@router.get("/roles", response_model=List[Role])
async def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("read", "role"))
):
    """Get all roles (requires 'read role' permission)"""
    roles = get_roles(db, skip=skip, limit=limit)
    return roles


@router.post("/roles", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_new_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("create", "role"))
):
    """Create a new role (requires 'create role' permission)"""
    db_role = get_role_by_name(db, role.name)
    if db_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )
    return create_role(db=db, role=role)


@router.get("/roles/{role_id}", response_model=Role)
async def read_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("read", "role"))
):
    """Get a specific role (requires 'read role' permission)"""
    db_role = get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return db_role


@router.put("/roles/{role_id}", response_model=Role)
async def update_existing_role(
    role_id: int,
    role: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("update", "role"))
):
    """Update a role (requires 'update role' permission)"""
    db_role = update_role(db, role_id=role_id, role=role)
    if db_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return db_role


@router.delete("/roles/{role_id}", response_model=Role)
async def delete_existing_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("delete", "role"))
):
    """Delete a role (requires 'delete role' permission)"""
    db_role = delete_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return db_role


# Permission endpoints
@router.get("/permissions", response_model=List[Permission])
async def read_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("read", "permission"))
):
    """Get all permissions (requires 'read permission' permission)"""
    permissions = get_permissions(db, skip=skip, limit=limit)
    return permissions


@router.post("/permissions", response_model=Permission, status_code=status.HTTP_201_CREATED)
async def create_new_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("create", "permission"))
):
    """Create a new permission (requires 'create permission' permission)"""
    db_permission = get_permission_by_details(db, permission.action, permission.resource)
    if db_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission for {permission.action} on {permission.resource} already exists"
        )
    return create_permission(db=db, permission=permission)


@router.delete("/permissions/{permission_id}", response_model=Permission)
async def delete_existing_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("delete", "permission"))
):
    """Delete a permission (requires 'delete permission' permission)"""
    db_permission = delete_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return db_permission


# User-Role management
@router.post("/users/roles", status_code=status.HTTP_200_OK)
async def assign_user_role(
    assignment: UserRoleAssign,
    db: Session = Depends(get_db),
    _: User = Depends(authorize("assign", "role"))
):
    """Assign a role to a user (requires 'assign role' permission)"""
    user = assign_role_to_user(db, assignment.user_id, assignment.role_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or role not found"
        )
    return {"message": f"Role assigned to user {user.id} successfully"}


@router.get("/users/me/permissions", response_model=List[Permission])
async def read_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's permissions"""
    permissions = get_user_permissions(db, current_user.id)
    return permissions