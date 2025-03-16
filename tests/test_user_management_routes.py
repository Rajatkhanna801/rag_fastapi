import pytest
from fastapi import status


@pytest.fixture
def auth_headers(client, admin_user):
    """Get token headers using admin user"""
    response = client.post(
        "/api/v1/auth/login",  # Updated path to include API prefix
        json={
            "email": admin_user.email,
            "password": "adminpassword"
        }
    )
    data = response.json()
    # Add error handling to see what's going wrong
    if "access_token" not in data:
        print("Login response:", data)
        raise ValueError(f"Failed to get token. Response: {data}")
    return {"Authorization": f"Bearer {data['access_token']}"}


def test_get_user_profile(client, auth_headers, test_user):
    # Print test data for debugging
    print(f"Testing get profile for user ID: {test_user.id}")
    
    response = client.get(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers
    )
    
    # Print response for debugging
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Check status and content
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["first_name"] == test_user.first_name
    assert data["last_name"] == test_user.last_name


def test_update_user_profile(client, auth_headers, test_user):
    # Print test data for debugging
    print(f"Testing update profile for user ID: {test_user.id}")
    
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "bio": "Updated bio"
    }
    
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers,
        json=update_data
    )
    
    # Print response for debugging
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Check status and content
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"
    assert data["bio"] == "Updated bio"


def test_delete_user_profile(client, auth_headers, test_user):
    # Print test data for debugging
    print(f"Testing delete profile for user ID: {test_user.id}")
    
    response = client.delete(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers
    )
    
    # Print response for debugging
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Check status
    assert response.status_code == status.HTTP_200_OK
    
    # Optional: Verify the user was actually deleted by trying to get it again
    get_response = client.get(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers
    )
    print("get_response", get_response)
    
    # The user should either be not found (404) or marked as deleted in the response
    if get_response.status_code == status.HTTP_200_OK:
        deleted_user = get_response.json()
        assert deleted_user["is_deleted"] == True
    else:
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_get_all_users(client, auth_headers, test_user, admin_user):
    # This endpoint is admin-only, so auth_headers should work
    response = client.get(
        "/api/v1/users/",
        headers=auth_headers
    )
    
    # Print response for debugging
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Check status and content
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Should contain at least our test user and admin user
    assert len(data) >= 2
    
    # Verify user emails are in the response
    user_emails = [user["email"] for user in data]
    assert test_user.email in user_emails
    assert admin_user.email in user_emails