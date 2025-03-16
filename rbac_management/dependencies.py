from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from oso import Oso
import os
import logging

from database import get_db
from models.user_models import User
from models.roles_permission import Role
from auth.main import get_current_user
from rbac_management.crud import get_user_permissions

# Set up logger
logger = logging.getLogger(__name__)

# Initialize Oso
oso = Oso()

def get_oso() -> Oso:
    """Get the global Oso instance."""
    return oso

# Define a simple Permission class
class Permission:
    def __init__(self, action, resource):
        self.action = action
        self.resource = resource

# Define a StringResource class to use with Oso
class StringResource:
    def __init__(self, name: str):
        self.name = name

# Load policy file
def init_oso():
    # Register classes with Oso
    oso.register_class(User)
    oso.register_class(Permission)
    oso.register_class(StringResource)
    oso.register_class(Role)
    
    # Define a minimal policy that follows Oso's expectations   
    policy = """
    # Define types
    actor User {}
    resource StringResource {}

    # Base allow rule for role-based permissions - notice the different syntax for checking role
    allow(user: User, action: String, resource: StringResource) if
        role = user.role and
        permission in role.permissions and
        permission.action = action and
        permission.resource = resource.name;

    # Allow users to access their own profile
    allow(user: User, "read", resource: StringResource) if
        resource.name = "user" and
        user.id = resource.id;

    # Superadmin override - also fixed
    allow(user: User, _action: String, _resource: StringResource) if
        role = user.role and
        role.name = "superadmin";
    """
    
    oso.load_str(policy)

# Call init on startup
init_oso()

# Authorization dependency
def authorize(action: str, resource: str):
    async def authorization_dependency(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        resource_instance = StringResource(resource)
        try:
            # Initialize Oso for each request
            oso = get_oso()
            is_allowed = oso.is_allowed(current_user, action, resource_instance)
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not authorized to {action} {resource}"
                )
            return current_user
        except Exception as e:
            logger.error(f"Authorization error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorization error"
            )
    
    return authorization_dependency