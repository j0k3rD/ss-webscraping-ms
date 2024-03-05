import os
from playwright.async_api import Page
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from ..data.constants import URL_ELECTRICITY_PROVIDER, NOT_FOUND, NO_DEBT, DEBT
from ..utils.scrap_utils.save_pdf_urls import save_pdf_urls


class ScrapDebtServicesEdemsa:
    def __init__(self, browser):
        self.browser = browser
        self.solver = recaptchaV2Proxyless()
        self.solver.set_verbose(1)
        self.solver.set_key(os.getenv("KEY_ANTICAPTCHA"))

    async def search(self, client_number):
        try:
            result = await self.scrap(client_number)
            print(result)
            if result[1] == None:
                result = await self.scrap(client_number)
            return result
        except Exception:
            return NOT_FOUND

    async def scrap(self, client_number):
        page = await self.browser.navigate_to_page(URL_ELECTRICITY_PROVIDER)
        await page.fill("#nic", str(client_number))
        sitekey_element = await page.query_selector(
            '//*[@id="consultaFacturas"]/div[2]/div'
        )
        sitekey_clean = await sitekey_element.get_attribute("data-sitekey")

        # Solve captcha
        self.solver.set_website_url(URL_ELECTRICITY_PROVIDER)
        self.solver.set_website_key(sitekey_clean)
        g_response = self.solver.solve_and_return_solution()

        if g_response != 0:
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
            await table_element.inner_html()

            await self.download_bills(page, client_number)
            return NO_DEBT
        except Exception:
            return DEBT, None
        finally:
            await page.close()

    async def download_bills(self, page: Page, client_number):
        await page.click("#pagas-tab")
        pdf_links = await page.query_selector_all("#fact_pagas_fuera_oficina")
        pdf_urls = [await link.get_attribute("href") for link in pdf_links]
        await save_pdf_urls(pdf_urls, client_number)
