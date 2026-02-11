"""
This file contains test fixtures for the application.
TestClient: A tool from FastAPI that lets you call your API endpoints directly in Python without running the actual server. 
MagicMock: A tool from unittest.mock that lets you mock objects and functions in your code.
"""

import os
import sys
from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

# Add src to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the database connection before importing main
sys.modules["motor.motor_asyncio"] = MagicMock()
sys.modules["motor.motor_asyncio"].AsyncIOMotorClient = MagicMock()

from main import app


@pytest.fixture(scope="module")
def test_client():
    client = TestClient(app)   # Create a "fake" web browser
    yield client               # Yield the client for use in tests
