import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports from the vacancies package
sys.path.append(str(Path(__file__).parent.parent))

from result import TinkoffLinkExtractor


async def test_extract_real_links(extractor):
    """Test that extractor gets more than zero links from real Tinkoff jobs page."""
    links = await extractor.get_links()

    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(link, str) for link in links)
    print(len(links))


if __name__ == "__main__":
    asyncio.run(test_extract_real_links(TinkoffLinkExtractor()))
