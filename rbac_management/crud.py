from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from models.roles_permission import Role, Permission, role_permissions
from models.user_models import User
from rbac_management.schemas import RoleCreate, RoleUpdate, PermissionCreate


# Role CRUD operations
def get_role(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    return db.query(Role).offset(skip).limit(limit).all()


def create_role(db: Session, role: RoleCreate) -> Role:
    # Create new role
    db_role = Role(
        name=role.name,
        description=role.description,
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)    
    # Add permissions to the role
    if role.permission_ids:
        permissions = db.query(Permission).filter(Permission.id.in_(role.permission_ids)).all()
        db_role.permissions = permissions
        db.commit()
        db.refresh(db_role)
    return db_role


def update_role(db: Session, role_id: int, role: RoleUpdate) -> Optional[Role]:
    db_role = get_role(db, role_id)
    if not db_role:
        return None    
    # Update role attributes
    if role.name is not None:
        db_role.name = role.name
    if role.description is not None:
        db_role.description = role.description
    # Update permissions if provided
    if role.permission_ids is not None:
        permissions = db.query(Permission).filter(Permission.id.in_(role.permission_ids)).all()
        db_role.permissions = permissions
    
    db_role.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_role)
    return db_role


def delete_role(db: Session, role_id: int) -> Optional[Role]:
    db_role = get_role(db, role_id)
    if not db_role:
        return None
    
    db.delete(db_role)
    db.commit()
    return db_role


# Permission CRUD operations
def get_permission(db: Session, permission_id: int) -> Optional[Permission]:
    return db.query(Permission).filter(Permission.id == permission_id).first()


def get_permission_by_details(db: Session, action: str, resource: str) -> Optional[Permission]:
    return db.query(Permission).filter(
        Permission.action == action,
        Permission.resource == resource
    ).first()


def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
    return db.query(Permission).offset(skip).limit(limit).all()


def create_permission(db: Session, permission: PermissionCreate) -> Permission:
    db_permission = Permission(
        name=permission.name,
        action=permission.action,
        resource=permission.resource
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


def delete_permission(db: Session, permission_id: int) -> Optional[Permission]:
    db_permission = get_permission(db, permission_id)
    if not db_permission:
        return None
    
    db.delete(db_permission)
    db.commit()
    return db_permission


# User-Role management
def assign_role_to_user(db: Session, user_id: int, role_id: int) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    role = get_role(db, role_id)
    
    if not user or not role:
        return None
    
    # Update user's role_id (assuming User model has a role_id field)
    user.role_id = role_id
    db.commit()
    db.refresh(user)
    return user


def get_user_permissions(db: Session, user_id: int) -> List[Permission]:
    """Get all permissions for a user based on their role"""
    user = db.query(User).filter(User.id == user_id).first()
    print("user000000000000000", user, user.role_id)
    if not user or not user.role_id:
        return []
    
    role = get_role(db, user.role_id)
    print("role", role, user.role_id)
    if not role:
        return []
    return role.permissions


def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
    return db.query(Permission).offset(skip).limit(limit).all()


def get_permission_by_details(db: Session, action: str, resource: str) -> Optional[Permission]:
    """Get a permission by its action and resource."""
    return db.query(Permission).filter(
        Permission.action == action,
        Permission.resource == resource
    ).first()

