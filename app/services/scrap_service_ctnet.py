from playwright.async_api import Page
from ..data.constants import URL_INTERNET_PROVIDER, NO_DEBT


class ScrapServicesCTNET:
    def __init__(self, browser):
        """
        Constructor de la clase

        param:
            - browser: Navegador que se va a utilizar para realizar la búsqueda
        """
        self.browser = browser

    async def search(self, client_number):
        url = URL_INTERNET_PROVIDER
        page = await self.browser.navigate_to_page(url)
        result = await self.parser(page, client_number)
        await page.close()
        return result

    async def parser(self, page: Page, client_number):
        await page.fill("#user", str(client_number))

        await page.click(".button_mictc_2")

        await page.click(".button_mictc_clientes")

        h2_element = await page.wait_for_selector(
            "div.listado-facturas.sucursal-page h2"
        )
        h2_text = await h2_element.inner_text()

        if NO_DEBT in h2_text:
            result = None
        else:
            result = h2_text

        return result
