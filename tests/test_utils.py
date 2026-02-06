"""
This file contains test cases for the utils module.
Unit Tests: Test the smallest pieces of your code in isolation.
    - test_load_config: Tests if the config is loaded correctly.
    - test_hash_password: Tests if the password is hashed correctly.
    - test_create_access_token: Tests if the access token is created correctly.
"""

import os

from jose import jwt

from src.utils import (
    create_access_token,
    generate_otp,
    hash_password,
    load_config,
    send_otp_email,
    verify_password,
)


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


def test_generate_otp():
    otp = generate_otp()
    assert isinstance(otp, str)
    assert len(otp) == 6
    assert otp.isdigit()


def test_send_otp_email():
    otp = generate_otp()
    email = os.getenv("TEST_EMAIL")
    assert send_otp_email(email, otp) is True
