import pytest
from loguru import logger

from app.link_extractor import BookingLinkExtractor, IndriverLinkExtractor, TinkoffLinkExtractor, WargamingLinkExtractor


@pytest.fixture
def mock_logger():
    return logger


@pytest.fixture
def extractor_booking(mock_logger):
    return BookingLinkExtractor(logger=mock_logger)


@pytest.fixture
def extractor_tinkoff(mock_logger):
    return TinkoffLinkExtractor(logger=mock_logger)


@pytest.fixture
def extractor_indriver(mock_logger):
    return IndriverLinkExtractor(logger=mock_logger)


@pytest.fixture
def extractor_wargaming(mock_logger):
    return WargamingLinkExtractor(logger=mock_logger)


@pytest.mark.asyncio
async def test_extract_real_links_booking(extractor_booking):
    """Test that extractor gets more than zero links from real Booking jobs page."""
    links = await extractor_booking.get_links()

    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(link, str) for link in links)
    print("booking", len(links))


@pytest.mark.asyncio
async def test_extract_real_links_tinkoff(extractor_tinkoff):
    """Test that extractor gets more than zero links from real Tinkoff jobs page."""
    links = await extractor_tinkoff.get_links()

    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(link, str) for link in links)
    print("tinkoff", len(links))


@pytest.mark.asyncio
async def test_extract_real_links_indriver(extractor_indriver):
    """Test that extractor gets more than zero links from real InDrive jobs page."""
    links = await extractor_indriver.get_links()

    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(link, str) for link in links)
    print("indriver", len(links))


@pytest.mark.asyncio
async def test_extract_real_links_wargaming(extractor_wargaming):
    """Test that extractor gets more than zero links from real Wargaming jobs page."""
    links = await extractor_wargaming.get_links()
    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(link, str) for link in links)
    print("wargaming", len(links))
