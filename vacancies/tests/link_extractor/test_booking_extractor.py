import pytest
from loguru import logger
from playwright.async_api import Page

from app.link_extractor.booking.extractor import BookingLinkExtractor


@pytest.fixture
def mock_logger():
    return logger


@pytest.fixture
def extractor(mock_logger):
    return BookingLinkExtractor(logger=mock_logger)


@pytest.mark.asyncio
async def test_name(extractor):
    """Test the name property returns correct value."""
    assert extractor.name == "Booking"


@pytest.mark.asyncio
async def test_load_all_content_success(extractor, mocker):
    """Test successful loading of content with pagination."""
    mock_page = mocker.AsyncMock(spec=Page)

    # Mock the selector wait
    mock_page.wait_for_selector = mocker.AsyncMock()

    # Mock finding links
    mock_page.eval_on_selector_all.side_effect = [
        ["link1", "link2"],  # First page
        ["link3", "link4"],  # Second page
        ["link5"],  # Last page
    ]

    # Mock next button behavior
    mock_next_button = mocker.AsyncMock()
    mock_next_button.is_disabled.side_effect = [False, False, True]
    mock_page.query_selector.return_value = mock_next_button

    await extractor._load_all_content(mock_page)

    assert len(extractor.all_links) == 5
    assert extractor.all_links == {"link1", "link2", "link3", "link4", "link5"}


@pytest.mark.asyncio
async def test_load_all_content_timeout(extractor, mocker):
    """Test handling of timeout during content loading."""
    mock_page = mocker.AsyncMock(spec=Page)
    mock_page.wait_for_selector.side_effect = TimeoutError()

    await extractor._load_all_content(mock_page)

    assert len(extractor.all_links) == 0


@pytest.mark.asyncio
async def test_extract_links(extractor, mocker):
    """Test extraction of collected links."""
    mock_page = mocker.AsyncMock(spec=Page)
    extractor.all_links = {"link1", "link2", "link3"}

    result = await extractor._extract_links(mock_page)

    assert isinstance(result, list)
    assert len(result) == 3
    assert set(result) == {"link1", "link2", "link3"}


@pytest.mark.asyncio
async def test_cleanup(extractor):
    """Test cleanup method."""
    await extractor._cleanup()


@pytest.mark.asyncio
async def test_extract_real_links(extractor):
    """Test that extractor gets more than zero links from real Booking jobs page."""
    links = await extractor.get_links()

    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(link, str) for link in links)
    print(len(links))
