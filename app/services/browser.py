from abc import ABC, abstractmethod
from playwright.sync_api import Browser as PlaywrightBrowser


class Browser(ABC):
    """
    Clase abstracta que define los métodos que deben implementar las clases que hereden de ella.
    """

    @abstractmethod
    def _get_browser(self) -> PlaywrightBrowser:
        """
        Método abstracto para obtener el navegador
        """
        pass

    @abstractmethod
    def navigate_to_page(self, url: str):
        """
        Método abstracto para buscar en el navegador

        param:
            - url: Url del sitio del servicio
        """
        pass

    @abstractmethod
    def close_browser(self):
        """
        Método abstracto para cerrar el navegador
        """
        pass
