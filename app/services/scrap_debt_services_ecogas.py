from playwright.async_api import Page
from anticaptchaofficial.recaptchav2proxyless import *
import os
from ..data.constants import URL_GAS_PROVIDER, TABLE_ERROR, NO_DEBT


class ScrapDebtServicesEcogas:
    def __init__(self, browser):
        self.browser = browser
        self.solver = recaptchaV2Proxyless()
        self.solver.set_verbose(1)
        self.solver.set_key(os.getenv("KEY_ANTICAPTCHA"))

    async def search(self, client_number):
        url = URL_GAS_PROVIDER
        page = await self.browser.navigate_to_page(url)

        await page.fill("#cliente", str(client_number))

        sitekey_element = await page.query_selector(
            '//*[@id="form_login_po"]/div[2]/div'
        )
        print("sitekey", sitekey_element)
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
            await page.click('//*[@id="boton_ingreso"]')

            try:
                table_element = await page.wait_for_selector(
                    ".table.table-hover.table-sm"
                )
                print(table_element)
                contenido = await table_element.inner_html()
                print(contenido)
                if "fdocdeu" in contenido:
                    print(contenido)
                else:
                    print(NO_DEBT)
            except Exception:
                print(TABLE_ERROR)

        else:
            print("task finished with error " + self.solver.error_code)

        await page.close()
