import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app  # Import your FastAPI app
from models.user_models import User
from models.roles_permission import Role, Permission
from auth.main import get_password_hash

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:  # Use context manager
        yield test_client
    
    # Clear any overrides after the test
    app.dependency_overrides.clear()

# @pytest.fixture(scope="function")
# def init_test_db(db):
#     """Initialize test database with required roles and permissions"""
#     # Create admin role
#     admin_role = Role(
#         name="admin",
#         description="Administrator role"
#     )
#     db.add(admin_role)
    
#     # Create user role
#     user_role = Role(
#         name="user",
#         description="Regular user role"
#     )
#     db.add(user_role)
    
#     db.commit()
#     return db


@pytest.fixture(scope="function")
def init_test_db(db):
    """Initialize test database with required roles and permissions"""
    # Create admin role
    admin_role = Role(
        name="admin",
        description="Administrator role"
    )
    db.add(admin_role)
    
    # Create user role
    user_role = Role(
        name="user",
        description="Regular user role"
    )
    db.add(user_role)
    
    db.commit()
    
    # Add basic permissions for testing
    from models.roles_permission import Permission
    
    # Create admin permission
    admin_all = Permission(
        name="admin_all",
        action="admin",
        resource="all"
    )
    db.add(admin_all)
    
    # Create user permissions
    read_user = Permission(
        name="read_user",
        action="read",
        resource="user"
    )
    db.add(read_user)
    
    update_user = Permission(
        name="update_user",
        action="update",
        resource="user"
    )
    db.add(update_user)
    
    delete_user = Permission(
        name="delete_user",
        action="delete",
        resource="user"
    )
    db.add(delete_user)
    
    db.commit()
    
    # Assign permissions to admin role
    admin_role.permissions = [admin_all, read_user, update_user, delete_user]
    db.commit()
    
    return db


@pytest.fixture(scope="function")
def test_user(init_test_db):
    db = init_test_db
    # Get the user role
    user_role = db.query(Role).filter(Role.name == "user").first()
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        first_name="Test",
        last_name="User",
        is_active=True,
        role_id=user_role.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def admin_user(init_test_db):
    db = init_test_db
    # Get the admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        role_id=admin_role.id
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@pytest.fixture
def token_headers(client, admin_user):
    """Get token headers using admin user"""
    response = client.post(
        "/auth/login",
        json={
            "email": admin_user.email,
            "password": "adminpassword"
        }
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"} 