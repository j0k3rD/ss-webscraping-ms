import os, asyncio
from playwright.async_api import Page
from playwright._impl._errors import TargetClosedError
from urllib.parse import urlparse, urlunparse, urljoin
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
import pdfplumber
from ..utils.scrap_utils.req_backend import save_bills
from ..utils.scrap_utils.get_selector import get_selector
from dotenv import load_dotenv
import time

load_dotenv()


class ScrapService:
    def __init__(self, browser):
        self.browser = browser
        self.solver = recaptchaV2Proxyless()
        self.solver.set_verbose(1)
        self.solver.set_key(os.getenv("KEY_ANTICAPTCHA"))
        self.global_bills = []
        self.save_bills_called = False
        self.debt = False

    async def search(self, data):
        url: str = data['service']['scrapping_config']['url']
        captcha: bool = data['service']['scrapping_config']['captcha']

        page = await self.browser.navigate_to_page(url)

        if captcha:
                captcha_sequence = data['service']['scrapping_config']['captcha_sequence']
                try: 
                    result = await self.parser(data, page, captcha_sequence)
                except Exception as e:
                    print(f"Error: {e}")
                    await page.close()
                    return await self.search(data)
        else:
            try:
                result = await self.parser(data, page)
            except Exception as e:
                print(f"Error: {e}")
                await page.close()
                return await self.search(data)
        await page.close()
        # Return debt status
        return self.debt, result

    async def parser(self, data, page: Page, captcha_sequence=None):
        client_number_index = 0
        client_number: str = data['provider_client']['client_code']
        provider_client_id: str = data['provider_client']['id']
        sequence: list = data['service']['scrapping_config']['sequence']
        
        try:
            if captcha_sequence:
                
                page.on("dialog", self.handle_dialog)
                page.on("download", self.handle_download)

                element_type = captcha_sequence[0]['element_type']
                selector = get_selector(captcha_sequence[0])
                sitekey_element_content = captcha_sequence[1]['content']
                captcha_button_content = captcha_sequence[2]['captcha_button_content']

                await page.fill(selector, str(client_number))
                sitekey_element = await page.query_selector(sitekey_element_content)
                sitekey_clean = await sitekey_element.get_attribute("data-sitekey")

                try:
                    await self.solve_captcha(data, page, sitekey_clean, captcha_button_content)
                except TimeoutError:
                    print("TimeoutError SCRAP. Reintentando...")
                    await page.close()
                    return await self.search(data)
        except KeyError:
            pass

        for i, action in enumerate(sequence):
            element_type = action['element_type']
            selector = get_selector(action)
            query = action['query']
            extra = action.get('extra', None)
            redirect = action.get('redirect', None)
            form = action.get('form', None)
            debt = action.get('debt', None)
            no_debt_text = action.get('no_debt_text', None)

            try:
                await page.wait_for_selector(selector, timeout=10000)
            except Exception:
                if i == len(sequence) - 1:
                    print('Last element not found, terminating process')
                    return
                else:
                    print('Element not found, skipping to next action')
                    continue

            if element_type == 'modal':
                try:
                    await page.click(selector)
                except Exception:
                    print('modal not found')

            elif element_type == 'input':
                try:
                    if action['size']:
                        size = int(action['size'])
                        input_value = client_number[client_number_index:client_number_index + size]
                        client_number_index += size
                except KeyError:
                    input_value = client_number
                await page.fill(selector, input_value)

            elif element_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'table', 'tbody', 'td', 'a', 'ul']:
                elements = await page.query_selector_all(selector)

                if elements and debt:
                    debt_message = await elements[0].inner_text()
                    if no_debt_text and (no_debt_text in debt_message):
                        self.debt = False
                    else:
                        self.debt = True

                if query and redirect:
                    href = await elements.get_attribute('href')
                    absolute_url = urljoin(page.url, href)
                    await page.goto(absolute_url, wait_until='load')

                elif query and form:
                    for i in range(0, 6, 2):
                        td = elements[i]
                        form = await td.query_selector("form")
                        await form.dispatch_event("submit")
                        await asyncio.sleep(12)

                elif query:
                    if extra == 'map':
                        elements_href = await page.eval_on_selector_all(selector, 'links => links.map(link => link.href)')
                    else:
                        elements_href = [await element.get_attribute('href') for element in elements]
                        
                    parsed_url = urlparse(page.url)
                    base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, "", "", "", ""))
                    
                    if extra == 'map':
                        elements_formatted = [{'url': href} for href in elements_href]
                    else:
                        elements_formatted = [{'url': urljoin(base_url, href)} for href in elements_href if href is not None]

                    result = await save_bills(provider_client_id, elements_formatted)
                    self.save_bills_called = True

                else:
                    await page.wait_for_selector(selector)
            elif element_type == 'button':
                await page.wait_for_selector(selector)
                await page.click(selector)
            elif element_type == 'buttons':
                buttons = await page.query_selector_all(selector)
                for button in buttons:
                    await button.click()

        if captcha_sequence and not self.save_bills_called:
            result = await save_bills(provider_client_id, self.global_bills)
        else:
            pass

        await page.close()

        return result


    async def solve_captcha(self, data, page, sitekey_clean, captcha_button_content):
        try:
            self.solver.set_website_url(page.url)
            self.solver.set_website_key(sitekey_clean)
            g_response = self.solver.solve_and_return_solution()
            if g_response != 0:
                await page.evaluate(
                    f"document.getElementById('g-recaptcha-response').innerHTML = '{g_response}'"
                )
                await page.click(captcha_button_content)
            else:
                print("task finished with error " + self.solver.error_code)
        except Exception as e:
            print("TimeoutError SOLVE CAPTCHA. Reintentando...")
            await page.close()
            return await self.search(data)

    async def handle_dialog(self, dialog):
        print(f"Dialog message: {dialog.message}")
        await dialog.accept()

    async def handle_download(self, download):
        time.sleep(2)
        print(f"Descargando: {download.suggested_filename}")
        try:
            path = await download.path()
        except TargetClosedError:
            print("La página, el contexto o el navegador se hanado antes de que se pudiera acceder a la ruta del archivo descargado.")
            return
        print(f"Guardado en: {path}")

        with pdfplumber.open(path) as pdf:
            pages = pdf.pages
            text = "".join(page.extract_text() for page in pages)
        self.global_bills.append({'content': text})
        time.sleep(2)
