"""
This file contains test cases for the user routes.
Integration Tests: Test the integration of different components of your code.
    - test_signup_success: Tests if the signup is successful.
    - test_signup_email_exists: Tests if the email already exists.
    - test_login_success: Tests if the login is successful.
    - test_login_invalid: Tests if the login is invalid.
    - test_logout: Tests if the logout is successful.
    - test_reset_password: Tests if the password is reset successfully.
    - test_delete_user: Tests if the user is deleted successfully.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.schemas import Token

# Mock the current user dependency for protected routes
async def mock_get_current_user():
    return {
        "_id": "user_id_123",
        "email": "test@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaW/j/j.6/j.6/j.6/j.6/j.6/j.6" # Dummy hash
    }

def test_signup_success(test_client):
    # Mock find_one to return None (no existing user)
    # Mock insert_one
    with patch("src.api_router.user_router.users_collection") as mock_collection:
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="new_id"))
        
        response = test_client.post("/auth/signup", json={
            "email": "new@example.com",
            "password": "strongpassword"
        })
        
        assert response.status_code == 201
        assert response.json() == {"message": "User created successfully"}
        mock_collection.find_one.assert_called_once()
        mock_collection.insert_one.assert_called_once()

def test_signup_email_exists(test_client):
    with patch("src.api_router.user_router.users_collection") as mock_collection:
        mock_collection.find_one = AsyncMock(return_value={"_id": "existing"})
        
        response = test_client.post("/auth/signup", json={
            "email": "existing@example.com",
            "password": "password"
        })
        
        assert response.status_code == 400
        assert response.json() == {"detail": "Email already registered"}

def test_login_success(test_client):
    # We need to use real hash_password or mock verify_password
    # It's easier to mock verify_password or use a known hash if utils uses passlib
    # Given utils.py uses passlib, let's mock verify_password to True
    
    with patch("src.api_router.user_router.users_collection") as mock_collection, \
         patch("src.api_router.user_router.verify_password", return_value=True):
        
        mock_collection.find_one = AsyncMock(return_value={
            "name": "Test User",
            "email": "test@example.com", 
            "hashed_password": "hashed"
        })
        
        response = test_client.post("/auth/login-json", json={
            "email": "test@example.com",
            "password": "password"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()

def test_login_invalid(test_client):
    with patch("src.api_router.user_router.users_collection") as mock_collection:
        mock_collection.find_one = AsyncMock(return_value=None) # User not found
        
        response = test_client.post("/auth/login-json", json={
            "email": "wrong@example.com",
            "password": "password"
        })
        
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid email or password"}

def test_logout(test_client):
    # Override dependency
    from src.api_router.user_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    response = test_client.post("/auth/logout")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}
    
    app.dependency_overrides = {}

def test_reset_password(test_client):
    from src.api_router.user_router import get_current_user, verify_password
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("src.api_router.user_router.users_collection") as mock_collection, \
         patch("src.api_router.user_router.verify_password", return_value=True):
         
        mock_collection.update_one = AsyncMock()
        
        response = test_client.put("/auth/reset-password", json={
            "old_password": "oldpass",
            "new_password": "newpass"
        })
        
        assert response.status_code == 200
        assert response.json() == {"message": "Password updated successfully"}
        
    app.dependency_overrides = {}

def test_delete_user(test_client):
    from main import app
    from src.api_router.user_router import get_current_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("src.api_router.user_router.users_collection") as mock_users, \
         patch("src.api_router.user_router.conversations_collection") as mock_convs, \
         patch("src.api_router.user_router.messages_collection") as mock_msgs:
        
        mock_users.delete_one = AsyncMock()
        mock_convs.delete_many = AsyncMock()
        mock_msgs.delete_many = AsyncMock()
        
        # Mock cursor for find
        mock_cursor = MagicMock()
        mock_cursor.__aiter__.return_value = []
        mock_convs.find.return_value = mock_cursor
        
        response = test_client.delete("/auth/delete-user")
        
        assert response.status_code == 200
        assert response.json() == {"message": "User and all associated data deleted successfully"}
        
    app.dependency_overrides = {}