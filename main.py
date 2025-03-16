from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from config import settings
from database import Base, engine, SessionLocal
from auth.routes import router as auth_router
from user_management.routes import router as user_router
from rbac_management.routes import router as rbac_router
from rag_management.routes import router as rag_router
from models.roles_permission import Role

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(user_router, prefix=settings.API_V1_STR)
app.include_router(rbac_router, prefix=settings.API_V1_STR)
app.include_router(rag_router, prefix=settings.API_V1_STR)


def initialize_roles():
    """Create default 'admin' and 'user' roles if they do not exist."""
    db: Session = SessionLocal()
    try:
        existing_roles = db.query(Role).filter(Role.name.in_(["admin", "user"])).all()
        existing_role_names = {role.name for role in existing_roles}

        roles_to_add = []
        if "admin" not in existing_role_names:
            roles_to_add.append(Role(name="admin", description="Administrator role"))

        if "user" not in existing_role_names:
            roles_to_add.append(Role(name="user", description="Standard user role"))

        if roles_to_add:
            db.add_all(roles_to_add)
            db.commit()
            print("✅ Default roles created: ", [role.name for role in roles_to_add])
        else:
            print("✅ Default roles already exist")

    finally:
        db.close()
        
        
def initialize_permissions():
    """Create default permissions for all resources in the system."""
    db: Session = SessionLocal()
    try:
        # Define all resources in the system
        resources = ["user", "role", "permission", "rag"]
        
        # Define standard actions for most resources
        standard_actions = ["create", "read", "update", "delete", "list"]
        
        # Define any special permissions
        special_permissions = [
            ("assign", "role"),  # For assigning roles to users
            ("admin", "all")     # Special admin permission for all resources
        ]
        
        # Build the list of all permissions
        permissions_to_create = []
        
        # Add standard CRUD permissions for each resource
        for resource in resources:
            for action in standard_actions:
                permission_name = f"{action}_{resource}"
                permissions_to_create.append({
                    "name": permission_name,
                    "action": action,
                    "resource": resource
                })
        
        # Add special permissions
        for action, resource in special_permissions:
            permission_name = f"{action}_{resource}"
            permissions_to_create.append({
                "name": permission_name,
                "action": action,
                "resource": resource
            })
        
        # Check which permissions already exist
        from rbac_management.crud import get_permission_by_details
        from models.roles_permission import Permission
        
        new_permissions = []
        for perm in permissions_to_create:
            existing = get_permission_by_details(db, perm["action"], perm["resource"])
            if not existing:
                new_permissions.append(
                    Permission(
                        name=perm["name"],
                        action=perm["action"],
                        resource=perm["resource"]
                    )
                )
        
        # Add new permissions to the database
        if new_permissions:
            db.add_all(new_permissions)
            db.commit()
            print(f"✅ Added {len(new_permissions)} new permissions")
        else:
            print("✅ All permissions already exist")
        
        # Assign all permissions to admin role
        from rbac_management.crud import get_role_by_name
        
        admin_role = get_role_by_name(db, "admin")
        if admin_role:
            # Get all permissions
            all_permissions = db.query(Permission).all()
            
            # Assign all permissions to admin role
            admin_role.permissions = all_permissions
            db.commit()
            print(f"✅ Assigned {len(all_permissions)} permissions to admin role")
    finally:
        db.close()
        
        
@app.on_event("startup")
def startup_event():
    """Run initialization tasks when the app starts."""
    initialize_roles()
    initialize_permissions()  


@app.get("/")
def root():
    return {"message": "Welcome to User Management API"}