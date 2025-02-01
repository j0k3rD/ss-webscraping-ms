from playwright.async_api import async_playwright, Browser as PlaywrightBrowser
from src.services.browser import Browser
from src.core.config import Config


class ChromeBrowser(Browser):
    """
    Clase que representa el navegador Chromium
    """

    def __init__(self):
        self.playwright = None
        self.browser = None

    async def _get_browser(self) -> PlaywrightBrowser:
        self.playwright = await async_playwright().start()
        endpoint_url = Config.ENDPOINT_PROXY

        # self.browser = await self.playwright.firefox.launch()
        self.browser = await self.playwright.chromium.connect_over_cdp(
            headless=True, endpoint_url=endpoint_url
        )
        return self.browser

    async def navigate_to_page(self, url: str):
        browser = await self._get_browser()
        browser_context = await browser.new_context(accept_downloads=True)
        page = await browser_context.new_page()
        # page = await browser.new_page()
        client = await page.context.new_cdp_session(page)

        await page.goto(url)
        return page, client
        # return page

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
