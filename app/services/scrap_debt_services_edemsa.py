from playwright.async_api import Page
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from ..data.constants import URL_ELECTRICITY_PROVIDER, NO_DEBT, DEBT
from ..utils.scrap_utils.save_pdf_urls import save_pdf_urls
from playwright.async_api import TimeoutError
import os


class ScrapDebtServicesEdemsa:
    def __init__(self, browser):
        self.browser = browser
        self.solver = recaptchaV2Proxyless()
        self.solver.set_verbose(1)
        self.solver.set_key(os.getenv("KEY_ANTICAPTCHA"))

    async def search(self, client_number):
        try:
            response = await self.scrap(client_number)
            return response
        except TimeoutError:
            print("TimeoutError SEARCH. Reintentando...")
            return await self.search(client_number)

    async def scrap(self, client_number):
        page = await self.browser.navigate_to_page(URL_ELECTRICITY_PROVIDER)
        await page.fill("#nic", str(client_number))
        sitekey_element = await page.query_selector(
            '//*[@id="consultaFacturas"]/div[2]/div'
        )
        sitekey_clean = await sitekey_element.get_attribute("data-sitekey")
        # Solve captcha
        await self.solve_captcha(page, sitekey_clean, client_number)
        try:
            response_scrap = await self.process_page(page, client_number)
            return response_scrap
        except TimeoutError:
            print("TimeoutError SCRAP. Reintentando...")
            await page.close()
            return await self.scrap(client_number)

    async def solve_captcha(self, page, sitekey_clean, client_number):
        try:
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
        except Exception:
            print("TimeoutError SOLVE CAPTCHA. Reintentando...")
            await page.close()
            return await self.scrap(client_number)

    async def process_page(self, page: Page, client_number):
        try:
            await page.click("#pagas-tab", timeout=10000)
        except TimeoutError:
            print("No se encontró el elemento #pagas-tab. Reintentando...")
            await page.close()
            return await self.scrap(client_number)

        await page.wait_for_selector(
            "#tfactura",
            state="visible",
        )
        pagination_index = 0
        all_pdf_urls = []
        while True:
            await page.wait_for_selector(".pagination", state="visible")
            pagination_elements = await page.query_selector_all(
                ".pagination .page-item a"
            )
            if pagination_index >= len(pagination_elements):
                break
            await pagination_elements[pagination_index].click()
            await page.wait_for_selector("#tfactura", state="visible")
            pdf_urls = await self.download_bills(page)
            all_pdf_urls.extend(pdf_urls)
            pagination_index += 1
        # Guarda todas las URLs después del bucle
        await save_pdf_urls(all_pdf_urls, client_number)
        await page.click("#impagas-tab")
        try:
            await page.wait_for_selector("#tfacturasImpagas", timeout=10000)
            debt_message = await page.inner_text("#tfacturasImpagas")
            if (
                "No existen facturas adeudadas para el nic seleccionado."
                in debt_message
            ):
                await page.close()
                return NO_DEBT
            else:
                await page.close()
                return DEBT
        except Exception:
            await page.close()
            return NO_DEBT

    async def download_bills(self, page: Page):
        await page.wait_for_selector("#fact_pagas_fuera_oficina", state="visible")
        pdf_elements = await page.query_selector_all("#fact_pagas_fuera_oficina")
        pdf_urls = await page.evaluate(
            """elements => elements.map(element => element.href)""",
            pdf_elements,
        )
        return pdf_urls
