from playwright.async_api import Page
from urllib.parse import urlparse, urlunparse
# from ..utils.scrap_utils.save_pdf_urls import save_pdf_urls


class ScrapService:
    def __init__(self, browser):
        self.browser = browser

    async def search(self, data):
        url: str = data['service']['scrapping_config']['url']
        client_number: str = data['provider_client']['client_code']
        sequence: list = data['service']['scrapping_config']['sequence']
        captcha: bool = data['service']['scrapping_config']['captcha'] #TODO: Implementar captcha

        page = await self.browser.navigate_to_page(url)
        result = await self.parser(page, sequence, client_number)
        await page.close()
        return result

    # async def download_bills(self, page: Page, client_number):
    #     pdf_links = await self.get_pdf_links(page)
    #     pdf_urls = [await link.get_attribute("href") for link in pdf_links]
    #     pdf_urls = self.format_pdf_urls(pdf_urls)
    #     await save_pdf_urls(pdf_urls, client_number)

    async def parser(self, page: Page, sequence, client_number):
        for action in sequence:
            element_type = list(action.keys())[0]
            print('element_type', element_type)
            element_info = action[element_type]
            selector = self.get_selector(element_info)
            query_all = element_info.get('query', False)

            await page.wait_for_selector(selector)

            if element_type == 'modal':
                await page.click(selector)
            elif element_type == 'input':
                await page.fill(selector, str(client_number))
            elif element_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'table', 'tbody', 'td', 'a']:
                if query_all:
                    elements = await page.query_selector_all(selector)
                    elements_href = [await element.get_attribute('href') for element in elements]
                    parsed_url = urlparse(page.url)
                    base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, "", "", "", ""))
                    elements_formatted = [{'url': base_url + href} for href in elements_href]
                    print(elements_formatted)
                    return elements_formatted 
                else:
                    await page.wait_for_selector(selector)
            elif element_type == 'button':
                await page.click(selector)
            elif element_type == 'tabla':
                await page.wait_for_selector(selector)
            else:
                print('element_type not found')
        # cerrar navegador
        await page.close()

    def get_selector(self, element):
        component_type = element['component_type']

        if component_type == 'id':
            selector = f"#{element['content']}"
        elif component_type == 'class':
            selector = f".{element['content']}"
        else:
            selector = element['content']
        print('selector', selector)
        return selector