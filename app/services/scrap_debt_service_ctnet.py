from playwright.async_api import Page
from ..data.constants import (
    URL_CTNET,
    NO_DEBT,
    DEBT,
    URL_CTNET_PDF,
)
from ..utils.scrap_utils.save_pdf_urls import save_pdf_urls


class ScrapDebtServicesCTNET:
    def __init__(self, browser):
        """
        Constructor de la clase

        param:
            - browser: Navegador que se va a utilizar para realizar la búsqueda
        """
        self.browser = browser

    async def search(self, client_number):
        url = URL_CTNET
        page = await self.browser.navigate_to_page(url)
        result = await self.parser(page, client_number)
        await page.close()
        return result

    async def parser(self, page: Page, client_number):
        # Quitar modal
        await page.click("#modalCookieSucursal .btn-close")

        await page.fill("#numero-cliente", str(client_number))

        await page.click(".btn-ctnet")

        # Quitar modal
        await page.click("#modalCookieSucursal .btn-close")

        await page.click(".btn-seleccionar-cliente")

        await self.download_bills(page, client_number)

        await page.wait_for_selector("#boton-tab-impagas")
        await page.click("#boton-tab-impagas")

        if await page.query_selector_all("#tabla-facturas-impagas tbody tr"):
            return DEBT
        else:
            return NO_DEBT

    async def download_bills(self, page: Page, client_number):

        await page.wait_for_selector("#boton-tab-pagas")
        await page.click("#boton-tab-pagas")

        await page.wait_for_selector("#tbody-facturas-pagas .td-center a")

        pdf_links = await page.query_selector_all("#tbody-facturas-pagas .td-center a")

        pdf_urls = [await link.get_attribute("href") for link in pdf_links]

        pdf_urls = [f"{URL_CTNET_PDF}{url}" for url in pdf_urls]

        await save_pdf_urls(pdf_urls, client_number)
