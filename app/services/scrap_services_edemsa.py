from app.services.browser import Browser
from .browser_firefox import FirefoxBrowser
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from flask import Blueprint, jsonify

# from app.constants import ScrapingServicesConstants as ScrapingConstants
import time
from anticaptchaofficial.recaptchav2proxyless import *


class ScrapServicesEdemsa:
    """
    Clase que representa el servicio de scraping (checkea facturas de edemsa)
    """

    def __init__(self, browser: Browser):
        """
        Constructor de la clase

        param:
            - browser: Navegador que se va a utilizar para realizar la búsqueda
        """
        self.browser = browser

    def search(self, client_number):
        url = "https://oficinavirtual.edemsa.com/login.php"
        self.browser.get(url)

        # Ingresar el número de cliente en el campo de texto
        nic_input = self.browser.find_element(By.ID, "nic")
        nic_input.send_keys(client_number)

        # Obtener el valor del sitio captcha
        sitekey_element = self.browser.find_element(
            By.XPATH, '//*[@id="consultaFacturas"]/div[2]/div'
        )
        sitekey_clean = sitekey_element.get_attribute("data-sitekey")

        # Resolver captcha utilizando el script de anticaptcha
        self.solve_captcha(sitekey_clean)

    def solve_captcha(self, sitekey_clean):
        solver = recaptchaV2Proxyless()
        solver.set_verbose(1)
        solver.set_key("6febdd44044bec146bc89db5f8943f72")
        solver.set_website_url(url)
        solver.set_website_key(sitekey_clean)

        g_response = solver.solve_and_return_solution()
        if g_response != 0:
            print("g-response: " + g_response)
            js_script = f"document.getElementById('g-recaptcha-response').innerHTML = '{g_response}'"
            self.browser.execute_script(js_script)
            self.browser.find_element(
                By.XPATH, '//*[@id="consultaFacturas"]/div[3]/button'
            ).click()
        else:
            print("task finished with error " + solver.error_code)

    # Mostrar al usuario los datos scrapeados
    def send_data(self, data):
        """
        Funcion que envia los datos scrapeados al usuario

        param:
            - data: Datos scrapeados
        """
        if len(data) == 0:
            return None
        else:
            return data

    # Cerrar el navegador
    def close_browser(self):
        """
        Funcion que cierra el navegador
        """
        self.browser.close()
