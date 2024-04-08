from playwright.async_api import Page
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from ..data.constants import URL_ELECTRICITY_PROVIDER, NO_DEBT, DEBT
from ..utils.scrap_utils.save_pdf_urls import save_pdf_urls
from playwright.async_api import TimeoutError
import os
import pdfplumber
import requests
import tempfile
import shutil
import re
import asyncio


class ScrapDebtServicesEdemsa:
    def __init__(self, browser):
        self.browser = browser
        self.solver = recaptchaV2Proxyless()
        self.solver.set_verbose(1)
        self.solver.set_key(os.getenv("KEY_ANTICAPTCHA"))
        self.global_bills = []

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
        while True:
            await page.wait_for_selector(".pagination", state="visible")
            pagination_elements = await page.query_selector_all(
                ".pagination .page-item a"
            )
            if pagination_index >= len(pagination_elements):
                break
            await pagination_elements[pagination_index].click()
            await page.wait_for_selector("#tfactura", state="visible")
            pdf_urls = await self.get_bills(page)
            self.global_bills.extend(pdf_urls)
            pagination_index += 1

        try:
            temp_dir = await self.download_pdf(self.global_bills)
            all_data = []
            files = await self.get_files_in_directory(temp_dir)
            for file in files:
                pdf_path = os.path.join(temp_dir, file)
                await self.extract_pdf_data(pdf_path, all_data)
            # Guarda todas las URLs después del bucle
            await save_pdf_urls(all_data, client_number)
        finally:
            shutil.rmtree(temp_dir)

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

    async def get_bills(self, page: Page):
        await page.wait_for_selector("#fact_pagas_fuera_oficina", state="visible")
        pdf_elements = await page.query_selector_all("#fact_pagas_fuera_oficina")
        pdf_urls = await page.evaluate(
            """elements => elements.map(element => element.href)""",
            pdf_elements,
        )
        return pdf_urls

    async def download_pdf(self, bills: list[str]):
        c = 1
        temp_dir = tempfile.mkdtemp()
        for bill in bills:
            print(bill)
            response = requests.get(bill)
            print(response.text)
            with open(os.path.join(temp_dir, f"{c}.pdf"), "wb") as file:
                file.write(response.content)
                c += 1
        return temp_dir

    async def get_files_in_directory(self, directory):
        """
        Obtiene la lista de archivos en un directorio dado.
        """
        return os.listdir(directory)

    async def extract_pdf_data(self, pdf_path, all_data: list[str]):
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
        return all_data.append(text)
