from app.services.browser import Browser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from anticaptchaofficial.recaptchav2proxyless import *
from flask import Flask, jsonify


class ScrapServicesEcogas:
    def __init__(self, browser: Browser):
        '''
        Constructor de la clase

        param:
            - browser: Navegador que se va a utilizar para realizar la búsqueda
        '''
        self.browser = browser

    def setup_browser(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        self.browser = webdriver.Chrome(options=chrome_options)

    def search(self):
        url = "https://autogestion.ecogas.com.ar/uiextranet/ingreso?s=p"
        self.browser.get(url)

        # Ingresamos el número de cliente en el campo de texto
        self.browser.find_element(By.ID, "cliente").send_keys(self.client_number)

        # Obtener el valor del sitio captcha
        sitekey = self.browser.find_element(By.XPATH, '//*[@id="form_login_po"]/div[2]/div')
        sitekey_clean = sitekey.get_attribute("data-sitekey")

        # Resolver captcha utilizando el script de anticaptcha
        self.solve_captcha(sitekey_clean)

    def solve_captcha(self, sitekey_clean):
        solver = recaptchaV2Proxyless()
        solver.set_verbose(1)
        solver.set_key("6febdd44044bec146bc89db5f8943f72")
        solver.set_website_url("https://autogestion.ecogas.com.ar/uiextranet/ingreso?s=p")
        solver.set_website_key(sitekey_clean)

        g_response = solver.solve_and_return_solution()
        if g_response != 0:
            print("g-response: " + g_response)
            js_script = f"document.getElementById('g-recaptcha-response').innerHTML = '{g_response}'"
            self.browser.execute_script(js_script)
            self.browser.find_element(By.XPATH, '//*[@id="boton_ingreso"]').click()
        else:
            print("task finished with error " + solver.error_code)

    def close_browser(self):
        if self.browser:
            self.browser.quit()