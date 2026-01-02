"""
This file contains test cases for the utils module.
Unit Tests: Test the smallest pieces of your code in isolation.
    - test_load_config: Tests if the config is loaded correctly.
    - test_hash_password: Tests if the password is hashed correctly.
    - test_create_access_token: Tests if the access token is created correctly.
"""

import pytest
from src.utils import hash_password, verify_password, create_access_token, load_config
from datetime import timedelta
from jose import jwt
import os

def test_load_config():
    config = load_config()
    assert isinstance(config, dict)
    assert "FastAPI" in config

def test_hash_password():
    password = "testpassword"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    assert isinstance(token, str)
    
    # Decode token to verify contents
    secret_key = os.getenv("JWT_SECRET_KEY")
    # We need to know the algorithm from config, but for test we can assume HS256 or mock it
    # Ideally we should load it from config like utils does
    config = load_config()
    algorithm = config["Security"]["ALGORITHM"]
    
    decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded
    assert "iat" in decoded
