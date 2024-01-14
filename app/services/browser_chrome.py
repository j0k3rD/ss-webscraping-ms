from playwright.async_api import async_playwright, Browser as PlaywrightBrowser
from app.services.browser import Browser


class ChromeBrowser(Browser):
    """
    Clase que representa el navegador Chromium
    """

    def __init__(self):
        self.playwright = None
        self.browser = None

    async def _get_browser(self) -> PlaywrightBrowser:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        return self.browser

    async def navigate_to_page(self, url: str):
        browser = await self._get_browser()
        page = await browser.new_page()
        await page.goto(url)
        return page

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
