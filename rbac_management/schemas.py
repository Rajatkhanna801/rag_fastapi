from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# Permission schemas
class PermissionBase(BaseModel):
    name: str
    action: str  # e.g., "read", "write", "delete"
    resource: str  # e.g., "user", "document", "setting"


class PermissionCreate(PermissionBase):
    pass


class Permission(PermissionBase):
    id: int

    class Config:
        from_attributes = True


# Role schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: List[int]


class RoleUpdate(RoleBase):
    permission_ids: Optional[List[int]] = None


class Role(RoleBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[Permission]

    class Config:
        from_attributes = True


# User role assignment schema
class UserRoleAssign(BaseModel):
    user_id: int
    role_id: int