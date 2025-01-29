import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from loguru import logger

# Import after environment variables are set
with patch.dict(
    "os.environ",
    {
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASS": "test_pass",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "GOOGLE_PROJECT_ID": "test-project",
        "GOOGLE_LOCATION": "test-location",
    },
):
    from app.data_extractor.processor import VacancyProcessor
    from app.db import VacancyRepository


@pytest.fixture
def mock_repository():
    repo = AsyncMock(spec=VacancyRepository)
    return repo


@pytest.fixture
def processor(mock_repository):
    return VacancyProcessor(
        vacancy_repository=mock_repository,
        max_input_tokens=1_000_000,
        max_output_tokens=1_000_000,
        num_workers=2,
        logger=logger,
    )


@pytest.mark.asyncio
async def test_processor_lifecycle(processor):
    """Test basic processor lifecycle (start/shutdown)."""
    await processor.start()
    await asyncio.sleep(1)  # Give time for workers to start
    await processor.shutdown()
