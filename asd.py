import asyncio
import json
import pickle
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://oficinavirtual.edemsa.com/")

        my_cookies = await page.context.cookies()

        # Guardar el almacenamiento local
        localStorage = await page.evaluate("() => JSON.stringify(localStorage)")
        with open('localStorage.json', 'w') as f:
            f.write(localStorage)

        # Limpiar el almacenamiento local
        await page.evaluate("localStorage.clear()")

        # Cargar el almacenamiento local
        with open('localStorage.json', 'r') as f:
            localStorage = f.read()
        localStorage = json.loads(localStorage)
        for key, value in localStorage.items():
            await page.evaluate(f"localStorage.setItem('{key}', '{json.dumps(value)}')")

        await page.context.clear_cookies()

        pickle.dump(my_cookies, open("cookies.pkl", "wb")) 

        cookies = pickle.load(open("cookies.pkl", "rb"))

        await page.context.add_cookies(cookies)

        await page.goto("https://oficinavirtual.edemsa.com/consulta_lista_factura.php?auth=MzA1MTExMw==")

        await asyncio.sleep(120)

        # Cerrar el navegador
        await browser.close()

# Ejecutar la función asincrónica
asyncio.run(main())