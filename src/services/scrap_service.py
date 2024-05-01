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
        client_number_index = 0
        for action in sequence:
            element_type = action['element_type']
            selector = self.get_selector(action)
            query_all = action['query']
            extra = action.get('extra', None)

            await page.wait_for_selector(selector)

            if element_type == 'modal':
                await page.click(selector)
            elif element_type == 'input':
                try:
                    if action['size']:
                        size = int(action['size'])
                        input_value = client_number[client_number_index:client_number_index + size]
                        client_number_index += size
                except KeyError:
                    input_value = client_number
                await page.fill(selector, input_value)
            elif element_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'table', 'tbody', 'td', 'a']:
                if query_all:
                    elements = await page.query_selector_all(selector)
                    if extra == 'map':
                        elements_href = await page.eval_on_selector_all(selector, 'links => links.map(link => link.href)')
                    else:
                        elements_href = [await element.get_attribute('href') for element in elements]
                    parsed_url = urlparse(page.url)
                    base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, "", "", "", ""))
                    if extra == 'map':
                        elements_formatted = [{'url': href} for href in elements_href]
                    else:
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
        await page.close()

    def get_selector(self, element):
        print('element', element)
        component_type = element['component_type']

        if component_type == 'id':
            selector = f"#{element['content']}"
        elif component_type == 'class':
            selector = f".{element['content']}"
        else:
            selector = element['content']
        print('selector', selector)
        return selector