from typing import Any, Optional


class HTTPClientError(Exception):
    """Custom exception for HTTP client errors."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, response: Any = None
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class WebScrapingError(Exception):
    """Base exception for web scraping errors"""

    pass


class CaptchaError(WebScrapingError):
    """Raised when there's an error with captcha handling"""

    pass


class BrowserError(WebScrapingError):
    """Raised when there's an error with browser operations"""

    pass


class ScrapingError(WebScrapingError):
    """Raised when there's an error during the scraping process"""

    pass
