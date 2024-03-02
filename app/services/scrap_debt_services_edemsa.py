from playwright.async_api import Page
from anticaptchaofficial.recaptchav2proxyless import *
import os
from ..data.constants import (
    URL_ELECTRICITY_PROVIDER,
    TABLE_ERROR,
    NO_DEBT,
    DEBT,
    NOT_FOUND,
)


class ScrapDebtServicesEdemsa:
    def __init__(self, browser):
        self.browser = browser
        self.solver = recaptchaV2Proxyless()
        self.solver.set_verbose(1)
        print(os.getenv("KEY_ANTICAPTCHA"))
        self.solver.set_key(os.getenv("KEY_ANTICAPTCHA"))

    async def search(self, client_number):
        url = URL_ELECTRICITY_PROVIDER
        page = await self.browser.navigate_to_page(url)

        await page.fill("#nic", str(client_number))

        sitekey_element = await page.query_selector(
            '//*[@id="consultaFacturas"]/div[2]/div'
        )
        sitekey_clean = await sitekey_element.get_attribute("data-sitekey")
        print(sitekey_clean)

        # Solve captcha
        self.solver.set_website_url(url)
        self.solver.set_website_key(sitekey_clean)

        g_response = self.solver.solve_and_return_solution()
        if g_response != 0:
            print("g-response: " + g_response)
            await page.evaluate(
                f"document.getElementById('g-recaptcha-response').innerHTML = '{g_response}'"
            )
            await page.click('//*[@id="consultaFacturas"]/div[3]/button')
        else:
            print("task finished with error " + self.solver.error_code)

        try:
            table_element = await page.wait_for_selector(
                "#tfacturasImpagas", timeout=60000
            )
            contenido = await table_element.inner_html()
            print(NO_DEBT)
            print(contenido)
        except:
            print(NOT_FOUND)

        await page.close()
