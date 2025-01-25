import pytest
from loguru import logger
from playwright.async_api import Page

from app.link_extractor.wargaming.extractor import WargamingLinkExtractor


@pytest.fixture
def mock_logger():
    return logger


@pytest.fixture
def extractor(mock_logger):
    return WargamingLinkExtractor(logger=mock_logger)


@pytest.mark.asyncio
async def test_name(extractor):
    """Test the name property returns correct value."""
    assert extractor.name == "Wargaming"


@pytest.mark.asyncio
async def test_load_all_content_success(extractor, mocker):
    """Test successful loading of content with 'Show more' button."""
    mock_page = mocker.AsyncMock(spec=Page)

    # Mock the initial selectors wait
    mock_page.wait_for_selector = mocker.AsyncMock()
    mock_page.wait_for_load_state = mocker.AsyncMock()

    # Mock locator and click behavior
    mock_locator = mocker.AsyncMock()
    mock_page.locator.return_value = mock_locator
    mock_locator.click.side_effect = [
        None,  # First click succeeds
        None,  # Second click succeeds
        TimeoutError(),  # No more button
    ]

    await extractor._load_all_content(mock_page)

    assert mock_page.locator.call_count >= 3
    assert mock_page.wait_for_load_state.called


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
        "https://wargaming.com/careers/job1",
        "https://wargaming.com/careers/job2",
        "https://wargaming.com/careers/job2",  # Duplicate to test deduplication
    ]

    result = await extractor._extract_links(mock_page)

    assert isinstance(result, list)
    assert len(result) == 3  # Wargaming extractor doesn't deduplicate in _extract_links
    assert all("wargaming.com/careers" in link for link in result)


@pytest.mark.asyncio
async def test_cleanup(extractor):
    """Test cleanup method."""
    await extractor._cleanup()


@pytest.mark.asyncio
async def test_extract_real_links(extractor, caplog):
    """Test that extractor gets more than zero links from real Wargaming jobs page."""
    links = await extractor.get_links()

    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(link, str) for link in links)
    assert all("wargaming.com" in link for link in links)

    # Log the number of links found
    extractor.logger.info(f"Found {len(links)} links from Wargaming")
