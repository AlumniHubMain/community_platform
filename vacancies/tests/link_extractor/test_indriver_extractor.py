import pytest
from loguru import logger
from playwright.async_api import Page

from app.link_extractor.indriver.extractor import InDriveLinkExtractor


@pytest.fixture
def mock_logger():
    return logger


@pytest.fixture
def extractor(mock_logger):
    return InDriveLinkExtractor(logger=mock_logger)


@pytest.mark.asyncio
async def test_name(extractor):
    """Test the name property returns correct value."""
    assert extractor.name == "InDrive"


@pytest.mark.asyncio
async def test_load_all_content_success(extractor, mocker):
    """Test successful loading of content with 'See more' button."""
    mock_page = mocker.AsyncMock(spec=Page)

    # Mock the initial selector wait
    mock_page.wait_for_selector = mocker.AsyncMock()

    # Mock 'See more' button behavior
    mock_button = mocker.AsyncMock()
    mock_page.wait_for_selector.side_effect = [
        mock_button,  # First click
        mock_button,  # Second click
        TimeoutError(),  # No more button
    ]

    await extractor._load_all_content(mock_page)

    # Verify that wait_for_selector was called multiple times
    assert mock_page.wait_for_selector.call_count >= 3


@pytest.mark.asyncio
async def test_load_all_content_timeout(extractor, mocker):
    """Test handling of timeout during initial content loading."""
    mock_page = mocker.AsyncMock(spec=Page)
    mock_page.wait_for_selector.side_effect = TimeoutError()

    await extractor._load_all_content(mock_page)


@pytest.mark.asyncio
async def test_extract_links(extractor, mocker):
    """Test extraction of links from the page."""
    mock_page = mocker.AsyncMock(spec=Page)
    mock_page.eval_on_selector_all.return_value = [
        "/vacancies/link1",
        "/vacancies/link2",
        "/vacancies/link2",  # Duplicate to test deduplication
    ]

    result = await extractor._extract_links(mock_page)

    assert isinstance(result, list)
    assert len(result) == 2  # Should be deduplicated
    assert set(result) == {"/vacancies/link1", "/vacancies/link2"}


@pytest.mark.asyncio
async def test_cleanup(extractor):
    """Test cleanup method."""
    await extractor._cleanup()


@pytest.mark.asyncio
async def test_extract_real_links(extractor):
    """Test that extractor gets more than zero links from real InDrive jobs page."""
    links = await extractor.get_links()

    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(link, str) for link in links)
    print(len(links))
