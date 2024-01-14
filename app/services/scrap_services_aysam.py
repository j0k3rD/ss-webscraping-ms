from playwright.async_api import Page
from ..data.constants import URL_WATER_PROVIDER, NO_DEBT, DEBT


class ScrapServicesAySaM:
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
        print(branch)
        account = client_number[3:10]
        print(account)
        subaccount = client_number[10:13]
        print(subaccount)
        digit = client_number[13]
        print(digit)
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

        await page.wait_for_selector("table")

        debt_element = page.query_selector("td.tdAVencer")

        if debt_element:
            return DEBT
        else:
            return NO_DEBT
