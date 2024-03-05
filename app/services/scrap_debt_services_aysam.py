from playwright.async_api import Page
from ..data.constants import URL_WATER_PROVIDER, NO_DEBT, DEBT, URL_AYSAM_PDF
from ..utils.scrap_utils.save_pdf_urls import save_pdf_urls


class ScrapDebtServicesAySaM:
    """
    Clase que representa el servicio de scraping (checkea facturas de aysam)
    """

    def __init__(self, browser):
        """
        Constructor de la clase

        Param:
            - browser: Navegador que se va a utilizar para realizar la búsqueda
        """
        self.browser = browser

    async def search(self, client_number):
        """
        Funcion que realiza la busqueda de la factura de aysam
        """
        client_number = str(client_number)

        branch = client_number[0:3]
        account = client_number[3:10]
        subaccount = client_number[10:13]
        digit = client_number[13]
        url = URL_WATER_PROVIDER
        page = await self.browser.navigate_to_page(url)
        bill_info = await self.parser(page, branch, account, subaccount, digit)
        await page.close()
        return bill_info

    async def parser(self, page: Page, branch, account, subaccount, digit):
        await page.click(".elementor-button-text")

        await page.fill("#camposucursal", branch)
        await page.fill("#campocuenta", account)
        await page.fill("#camposubcuenta", subaccount)
        await page.fill("#campodigito", digit)

        await page.click('//input[@type="submit" and @class="btn-flecha gris"]')
        try:
            await page.wait_for_selector("table a", state="visible", timeout=1000)
        except Exception:
            return NO_DEBT

        client_number = branch + account + subaccount + digit
        await self.download_bills(page, client_number=client_number)
        return DEBT

    async def download_bills(self, page: Page, client_number):
        """
        Funcion que descarga las facturas de aysam
        """
        await page.query_selector(".tdAVencer")

        pdf_urls = await page.eval_on_selector_all(
            "table a", "links => links.map(link => link.href)"
        )
        # Borramos los duplicados
        pdf_urls = list(set(pdf_urls))

        print(pdf_urls)

        await save_pdf_urls(pdf_urls, client_number)
