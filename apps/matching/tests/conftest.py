import pytest
from unittest.mock import patch
import os


@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing"""
    with patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "development",
            "PROJECT_ID": "test-project",
            "BASE_URL": "http://localhost:8000",
        },
    ):
        yield
