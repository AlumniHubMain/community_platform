from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings before any test modules are imported."""
    mock_settings = {
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASS": "test_pass",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "GOOGLE_PROJECT_ID": "test-project",
        "GOOGLE_LOCATION": "test-location",
    }

    with patch.dict("os.environ", mock_settings):
        yield mock_settings
