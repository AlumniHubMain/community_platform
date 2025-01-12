"""Extractor for Booking vacancy links."""

import asyncio

from playwright.async_api import Page

from src.link_extractor.base import BaseLinkExtractor


class BookingLinkExtractor(BaseLinkExtractor):
    """Extractor for Booking vacancy links."""
    def __init__(self):
        super().__init__("https://jobs.booking.com/booking/jobs")
        self.all_links = set()

    async def _accept_cookies(self, page: Page) -> None:
        try:
            # Если появится кнопка принятия cookies, добавим её здесь
            pass
        except Exception as e:
            self.logger.info("No cookie consent button found:", e)

    async def _load_all_content(self, page: Page) -> None:
        try:
            # Ждем загрузки основного контента и убеждаемся, что загрузились все элементы
            await page.wait_for_selector('a[href*="/booking/jobs/"]', timeout=self.timeout)
            await page.wait_for_load_state("networkidle")

            while True:
                # Собираем ссылки с текущей страницы
                current_links = await page.eval_on_selector_all(
                    'a[href*="/booking/jobs/"]', "elements => elements.map(el => el.getAttribute('href'))"
                )
                self.all_links.update(current_links)  # Добавляем новые ссылки в общий набор
                self.logger.info(
                    f"Found {len(current_links)} vacancies on current page. Total unique links: {len(self.all_links)}"
                )

                try:
                    next_button = await page.query_selector(
                        "button.mat-focus-indicator.mat-tooltip-trigger"
                        ".mat-paginator-navigation-next.mat-icon-button"
                        ".mat-button-base"
                    )

                    if not next_button or await next_button.is_disabled():
                        self.logger.info("No more pages available")
                        break

                    await next_button.click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_selector('a[href*="/booking/jobs/"]', timeout=self.timeout)
                    await asyncio.sleep(2)
                except Exception as e:
                    self.logger.info(f"Error during pagination: {e}")
                    break

        except TimeoutError as e:
            self.logger.info(f"Timeout while loading content: {e}")

    async def _extract_links(self, page: Page) -> list[str]:
        # Возвращаем собранные ссылки
        return list(getattr(self, "all_links", set()))

    async def get_links(self) -> list[str]:
        """Get all collected links."""
        return list(self.all_links)
