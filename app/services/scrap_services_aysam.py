from flask import Blueprint, jsonify
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from main.services.browser import Browser
from .browser_firefox import FirefoxBrowser
from main.constants import ScrapingServicesConstants as ScrapingConstants


class ScrapServicesAySaM:
    """
    Clase que representa el servicio de scraping (checkea facturas de aysam)
    """
    def __init__(self, browser: Browser):
        """
        Constructor de la clase

        Param:
            - browser: Navegador que se va a utilizar para realizar la búsqueda
        """
        self.browser = browser

    def search(self):
        """
        Funcion que realiza la busqueda de la factura de aysam
        """
        url = 'https://aysam.com.ar/'
        web_page = self.browser.search(url)
        bill_info = self.parser(web_page)
        response = self.send_data(bill_info)
        web_page.close()
        return response

    def send_data(self, data):
        """
        Funcion que envia los datos scrapeados al usuario

        Param:
            - data: Datos scrapeados
        """
        if not data:
            return None
        else:
            return data

    def close_browser(self):
        """
        Funcion que cierra el navegador
        """
        self.browser.close()

    def get_bill(self, client_number, web_page: WebDriver):
        """
        Funcion que obtiene la factura de aysam

        Param:
            - client_number: Numero de cliente
            - web_page: Página web
        """
        #! Traer client_number de los files de la app
        
        # Click en paga factura
        web_page.find_element(By.CLASS_NAME, 'elementor-button-text').click()

        # Ingresar campo sucursal
        web_page.find_element(By.ID, "camposucursal").send_keys("")
        web_page.find_element(By.ID, "campocuenta").send_keys("")
        web_page.find_element(By.ID, "camposubcuenta").send_keys("")
        web_page.find_element(By.ID, "campodigito").send_keys("")

        web_page.find_element(By.XPATH, '//input[@type="submit" and @class="btn-flecha gris"]').click()