from flask import Blueprint, render_template
from selenium import webdriver

web_scraping_bp = Blueprint('web_scraping', __name__)

@web_scraping_bp.route('/aysam')
def scrape_aysam():
    driver_path = '/usr/local/bin/geckodriver'
    driver = webdriver.Chrome(executable_path=driver_path)

    # Ejemplo de scraping (reemplaza con tu lógica de scraping)
    driver.get('https://www.ejemplo.com')
    contenido = driver.page_source

    driver.quit()

    return render_template('scrape_result.html', content=contenido)