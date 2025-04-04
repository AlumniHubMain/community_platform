import pytest
from picologging import Logger
from playwright.async_api import Browser, BrowserContext, Page

from app.core.data_extractor.extractor import VacancyExtractor
from app.core.data_extractor.structure_vacancy import VacancyStructure


@pytest.fixture
def mock_logger():
    return Logger("test_vacancy_extractor")


@pytest.fixture
def extractor(mock_logger):
    return VacancyExtractor(logger=mock_logger)


@pytest.mark.asyncio
async def test_process_vacancy_page_error(extractor, mocker):
    """Test handling of page loading errors."""
    mock_page = mocker.AsyncMock(spec=Page)
    mock_context = mocker.AsyncMock(spec=BrowserContext)
    mock_browser = mocker.AsyncMock(spec=Browser)
    mock_playwright = mocker.AsyncMock()

    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    # Simulate page loading error
    mock_page.goto.side_effect = Exception("Failed to load page")

    result = await extractor.process_vacancy("fucking error")
    assert result is None


def test_get_current_tokens(extractor):
    """Test token counting."""
    input_tokens, output_tokens = extractor.get_current_tokens()
    assert isinstance(input_tokens, int)
    assert isinstance(output_tokens, int)
    assert input_tokens > 0
    assert output_tokens > 0


@pytest.mark.asyncio
async def test_process_real_vacancy(extractor, caplog):
    """Test processing of a real vacancy URL."""
    # Use a known stable job posting URL
    urls = [
        "https://wargaming.com/en/careers/vacancy_2840632_belgrade/",
        "https://jobs.booking.com/booking/jobs/16148?lang=en-us",
        "https://careers.indrive.com/vacancies/ae647d53ca703e6a3e4082c32bdc394c",
    ]

    for url in urls:
        result = await extractor.process_vacancy(url)

        assert isinstance(result, VacancyStructure)
        assert result.title is not None
        assert result.description is not None

        extractor.logger.info(f"Successfully extracted vacancy: {result.title}")
