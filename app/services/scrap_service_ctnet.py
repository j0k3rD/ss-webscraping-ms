from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify


class ScrapServicesCTNET:
    def __init__(self, client_number):
        self.client_number = client_number
        self.browser = None

    def setup_browser(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        self.browser = webdriver.Chrome(options=chrome_options)

    def search(self):
        url = 'https://www.cabletelevisoracolor.com/clientes.php'
        self.browser.get(url)

        # Ingresamos el número de cliente en el campo de texto
        user_input = self.browser.find_element(By.ID, "user")
        user_input.click()
        user_input.send_keys(self.client_number)

        # Hacemos clic en el botón de login
        self.browser.find_element(By.CLASS_NAME, 'button_mictc_2').click()

        # Pausa para verificar el resultado en el navegador
        input("Presiona Enter después de verificar el resultado...")

    def close_browser(self):
        if self.browser:
            self.browser.quit()