import asyncio
from playwright.async_api import async_playwright


class Scraper:
    def __init__(self, solver):
        self.solver = solver

    async def solve_captcha(self, page, sitekey_clean, captcha_button_content):
        try:
            print("Solving captcha...")
            self.solver.set_website_url(page.url)
            self.solver.set_website_key(sitekey_clean)
            g_response = self.solver.solve_and_return_solution()
            if g_response != 0:
                print(f"Captcha solved: {g_response}")
                await page.evaluate(
                    f"document.getElementById('g-recaptcha-response').innerHTML = '{g_response}'"
                )
                await page.click(captcha_button_content)
            else:
                print("Task finished with error " + self.solver.error_code)
        except Exception as e:
            print(f"Error solving captcha: {e}")
            print("Skipping captcha solving...")

    async def run(self, playwright):
        browser = await playwright.firefox.launch(headless=False)
        page = await browser.new_page()
        await page.goto("")

        await asyncio.sleep(2)

        # Cerrar el modal de cookies
        await page.click("#modalCookieSucursal .btn-close")
        await asyncio.sleep(2)

        # Interactuar con el input del número de cliente
        await page.fill("#numero-cliente", "")
        await asyncio.sleep(2)

        # Hacer clic en el botón para mostrar el captcha
        captcha_button_content = "//*[@id='submitButton']"
        await page.click(captcha_button_content)
        await asyncio.sleep(2)

        # Resolver el captcha si aparece
        try:
            sitekey_clean = ""  # Replace with actual site key
            await self.solve_captcha(page, sitekey_clean, captcha_button_content)
        except Exception as e:
            print(f"Captcha not found or error occurred: {e}")
        await asyncio.sleep(2)

        # Cerrar el modal de cookies
        await page.click("#modalCookieSucursal .btn-close")
        await asyncio.sleep(2)

        # Hacer clic en el botón de seleccionar cliente
        await page.click(".btn-seleccionar-cliente")
        await asyncio.sleep(2)

        # Buscar texto de facturas impagas
        debt_rows = await page.query_selector_all("#avisoImpagasCliente")
        for row in debt_rows:
            print(await row.text_content())
        await asyncio.sleep(2)

        # Hacer clic en el botón de facturas pagas
        await page.click("#btnTabPagas")
        await asyncio.sleep(2)

        # Extraer enlaces de facturas pagas
        paid_links = await page.query_selector_all("#tbodyFacturasPagas .td-center a")
        for link in paid_links:
            print(await link.get_attribute("href"))

        await browser.close()


async def main():
    solver = None  # Initialize your captcha solver here
    scraper = Scraper(solver)
    async with async_playwright() as playwright:
        await scraper.run(playwright)


asyncio.run(main())
