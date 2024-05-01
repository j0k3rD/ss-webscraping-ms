from playwright.async_api import Page
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
import os
from urllib.parse import urljoin
from ..data.constants import URL_GAS_PROVIDER, NO_DEBT, DEBT
import pdfplumber
import asyncio
from ..utils.scrap_utils.save_pdf_urls import save_pdf_urls


class ScrapDebtServicesEcogas:
    def __init__(self, browser):
        self.browser = browser
        self.solver = recaptchaV2Proxyless()
        self.solver.set_verbose(1)
        self.solver.set_key(os.getenv("KEY_ANTICAPTCHA"))
        self.global_bills = []

    async def handle_dialog(self, dialog):
        print(f"Dialog message: {dialog.message}")
        await dialog.accept()

    async def handle_download(self, download):
        print(f"Descargando: {download.suggested_filename}")
        path = await download.path()
        print(f"Guardado en: {path}")

        with pdfplumber.open(path) as pdf:
            pages = pdf.pages
            text = "".join(page.extract_text() for page in pages)

        self.global_bills.append(text)

    async def search(self, client_number):
        try:
            response = await self.scrap(client_number)
            return response
        except TimeoutError:
            print("TimeoutError SEARCH. Reintentando...")
            return await self.search(client_number)

    async def scrap(self, client_number):
        url = URL_GAS_PROVIDER
        page = await self.browser.navigate_to_page(url)

        page.on("dialog", self.handle_dialog)
        page.on("download", self.handle_download)

        await page.fill("#cliente", str(client_number))

        sitekey_element = await page.query_selector(
            '//*[@id="form_login_po"]/div[2]/div'
        )
        print("sitekey", sitekey_element)
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

    async def process_page(self, page: Page, client_number):

        debt_message = None

        try:
            close_button = page.wait_for_selector(
                "#modalFormActDatos .close", state="attached", timeout=10000
            )
            close_button.click()
        except Exception:
            print("No se encontro modal")

        try:
            msg_element = await page.query_selector("#alert-msj")
            await msg_element.inner_text()
        except Exception:
            debt_message = NO_DEBT

        try:
            link = await page.wait_for_selector(
                "a.black-text.d-flex.justify-content-end", timeout=10000
            )
            href = await link.get_attribute("href")
        except Exception:
            print("No se encontro link")
            await page.close()
            return await self.scrap(client_number)

        absolute_url = urljoin(URL_GAS_PROVIDER, href)

        await page.goto(absolute_url)

        td_elements = await page.query_selector_all("td[style='font-size:18px;']")

        for i in range(0, 6, 2):
            td = td_elements[i]
            form = await td.query_selector("form")
            await form.dispatch_event("submit")
            await asyncio.sleep(12)

        debt_message = DEBT

        await page.close()
        await save_pdf_urls(self.global_bills, client_number)

        return debt_message

    async def solve_captcha(self, page, sitekey_clean, client_number):
        try:
            self.solver.set_website_url(URL_GAS_PROVIDER)
            self.solver.set_website_key(sitekey_clean)
            g_response = self.solver.solve_and_return_solution()
            if g_response != 0:
                await page.evaluate(
                    f"document.getElementById('g-recaptcha-response').innerHTML = '{g_response}'"
                )
                await page.click('//*[@id="boton_ingreso"]')
            else:
                print("task finished with error " + self.solver.error_code)
        except Exception:
            print("TimeoutError SOLVE CAPTCHA. Reintentando...")
            await page.close()
            return await self.scrap(client_number)
