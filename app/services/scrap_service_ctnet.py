from app.services.browser import Browser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver


class ScrapServicesCTNET:
    def __init__(self, browser: Browser):
        """
        Constructor de la clase

        param:
            - browser: Navegador que se va a utilizar para realizar la búsqueda
        """
        self.browser = browser

    def search(self, client_number):
        url = "https://www.cabletelevisoracolor.com/clientes.php"
        html = self.browser.navegate_to_page(url)
        result = self.parser(html, client_number)
        html.close()
        return result

    def parser(self, html: WebDriver, client_number):
        user_input = html.find_element(By.ID, "user")
        user_input.click()
        user_input.send_keys(client_number)

        html.find_element(By.CLASS_NAME, "button_mictc_2").click()

        time.sleep(2)

        html.find_elements(By.CLASS_NAME, "button_mictc_clientes")[0].click()

        WebDriverWait(html, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@class="listado-facturas sucursal-page"]/h2')
            )
        )

        h2_text = html.find_element(
            By.XPATH, '//div[@class="listado-facturas sucursal-page"]/h2'
        ).text

        if "EL CLIENTE NO REGISTRA DEUDA." in h2_text:
            result = None
        else:
            result = h2_text

        return result
