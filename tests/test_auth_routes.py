import pytest
from fastapi import status


def test_signup(client, db):
    """Test user signup with role creation if needed"""
    # Create roles if they don't exist (similar to your main app initialization)
    from models.roles_permission import Role
    
    # Check if user role exists
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        # Create user role
        user_role = Role(name="user", description="Standard user role")
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
    
    # Check if admin role exists
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        # Create admin role
        admin_role = Role(name="admin", description="Administrator role")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
    
    # Now attempt signup
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test_user@yopmail.com",
            "password": "strongpassword123",
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Software developer"
        }
    )
    
    # Check response
    assert response.status_code == 201  # HTTP_201_CREATED
    data = response.json()
    print("data", data)
    assert "user_id" in data
    assert data["message"] == "User created successfully"
    assert data["role"] == "user"  # Verify correct role was assigned


def test_login(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.fixture
def auth_headers(client, test_user):
    """Fixture to get authentication headers"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    tokens = login_response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}

def test_change_password(client, auth_headers, test_user):
    response = client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": "testpassword",
            "new_password": "newpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Password changed successfully"

def test_logout(client, auth_headers):
    response = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Successfully logged out"

# Add negative test cases
def test_login_with_wrong_credentials(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_signup_with_existing_email(client, test_user):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",  # Same email as test_user
            "password": "newpassword",
            "first_name": "New",
            "last_name": "User",
            "bio": "Test bio"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST 