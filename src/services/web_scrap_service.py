from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import re
from urllib.parse import urljoin, urlparse, urlunparse

import pdfplumber
from playwright.async_api import Page, Download
from playwright._impl._errors import TargetClosedError
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless

from src.core.errors import BrowserError, CaptchaError, ScrapingError
from src.core.config import Config
from src.core.logging_config import setup_logging
from src.core.retries import with_retry
from src.services.http_client import MainServiceClient
from src.utils.get_selector import get_selector
from src.utils.browser_invoker import InvokerBrowser
from src.services.bill_service import BillService


@dataclass
class ScrapingConfig:
    """Configuration for web scraping operations."""

    url: str
    captcha: bool
    captcha_sequence: List[Dict[str, Any]] = field(default_factory=list)
    sequence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UserService:
    """User service information."""

    id: str
    user_id: str
    service_id: str
    customer_number: str
    created_at: str
    updated_at: str


class WebScrapService:
    """
    Enhanced web scraping service with improved error handling, logging, and best practices.

    This service handles web scraping operations including:
    - Browser automation
    - Captcha solving
    - PDF downloading and processing
    - Bill data extraction and storage
    """

    def __init__(self):
        """Initialize the web scraping service with necessary dependencies."""
        self.logger = setup_logging("web_scraping_service")
        self.http_client = MainServiceClient()
        self.bill_service = BillService()
        self.browser = None
        self.debt = False
        self.bills: List[Dict[str, Any]] = []
        self.save_bills_called = False
        self.downloaded_files = set()

        # Initialize captcha solver if needed
        self.solver = recaptchaV2Proxyless()
        self.solver.set_verbose(1)
        self.solver.set_key(Config.KEY_ANTICAPTCHA)

    async def __aenter__(self):
        """Context manager entry point."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point with cleanup."""
        if exc_type is not None:
            self.logger.error(f"Error during context exit: {exc_val}")
        await self.cleanup()

    async def cleanup(self) -> None:
        """Clean up resources and close browser."""
        try:
            if self.browser:
                await self.browser.close_browser()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    async def _initialize_browser(self, config: ScrapingConfig):
        """Initialize browser based on configuration"""
        try:
            invoker = InvokerBrowser()
            browser_type = (
                "firefox" if config.captcha and config.captcha_sequence else "chrome"
            )
            self.browser = invoker.get_command(browser_type)
            return self.browser
        except Exception as e:
            self.logger.error(f"Browser initialization failed: {str(e)}")
            raise BrowserError(f"Browser initialization failed: {str(e)}")

    async def _navigate_to_page(self, browser, url: str):
        """Navigate to target page with error handling"""
        try:
            page_result = await browser.navigate_to_page(url)
            return (
                page_result if isinstance(page_result, tuple) else (page_result, None)
            )
        except Exception as e:
            self.logger.error("Navigation failed: %s", str(e))
            raise BrowserError(f"Navigation failed: {str(e)}")

    async def _handle_dialog(self, dialog) -> None:
        """Handle browser dialogs automatically."""
        await asyncio.sleep(2)
        await dialog.accept()

    async def _handle_download(self, download: Download) -> None:
        """
        Handle file downloads and process PDFs.

        Args:
            download: Playwright download object
        """
        await asyncio.sleep(2)
        try:
            path = await download.path()
            filename = download.suggested_filename

            if filename in self.downloaded_files:
                self.logger.info(f"Skipping duplicate download: {filename}")
                return

            self.downloaded_files.add(filename)

            # Process PDF content
            with pdfplumber.open(path) as pdf:
                text = "".join(page.extract_text() for page in pdf.pages)

            self.bills.append({"content": text})
            self.logger.info(f"Successfully processed PDF: {filename}")

        except TargetClosedError:
            self.logger.error("Target closed before download could complete")
        except Exception as e:
            self.logger.error(f"Error processing download: {str(e)}")

    @with_retry(max_retries=3)
    async def search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for scraping operations.

        Args:
            data: Dictionary containing scraping configuration and user service data

        Returns:
            Dict containing debt status, save results, and extraction flags

        Raises:
            ScrapingError: If scraping operation fails
        """
        self.logger.info("Starting search operation")
        try:
            config = ScrapingConfig(**data["service"]["scraping_config"])
            user_service = UserService(**data["user_service"])

            # Initialize browser and navigate to page
            browser = await self._initialize_browser(config)
            page_result = await self._navigate_to_page(browser, config.url)

            result = await self._handle_scraping(page_result, config, user_service)
            save_result = await self._process_and_save_results(result, user_service.id)

            return self._prepare_response(save_result)

        except Exception as e:
            self.logger.error(f"Search operation failed: {str(e)}")
            raise ScrapingError(f"Search operation failed: {str(e)}")

    async def _solve_captcha_with_sequence(
        self, page: Page, config: ScrapingConfig, user_service: UserService
    ) -> None:
        """
        Handle captcha solving using sequence configuration.

        Args:
            page: Playwright page object
            config: Scraping configuration
            user_service: User service information
        """
        try:
            # Wait for customer number input field
            await page.wait_for_selector(
                get_selector(config.captcha_sequence[0]), timeout=3000
            )

            # Fill in customer number
            await page.fill(
                get_selector(config.captcha_sequence[0]),
                str(user_service.customer_number),
            )

            # Get captcha sitekey
            sitekey_element = await page.query_selector(
                config.captcha_sequence[1]["content"]
            )
            sitekey = await sitekey_element.get_attribute("data-sitekey")

            # Solve captcha
            self.solver.set_website_url(page.url)
            self.solver.set_website_key(sitekey)
            g_response = self.solver.solve_and_return_solution()

            if g_response != 0:
                self.logger.info(f"Captcha solved successfully")
                await page.evaluate(
                    f"document.getElementById('g-recaptcha-response').innerHTML = '{g_response}'"
                )
                await page.click(config.captcha_sequence[2]["captcha_button_content"])
            else:
                raise CaptchaError(f"Captcha solving failed: {self.solver.error_code}")

        except Exception as e:
            self.logger.error(f"Captcha solving failed: {str(e)}")
            raise CaptchaError(str(e))

    async def _wait_for_captcha_solve(self, client) -> None:
        """Wait for manual captcha solving."""
        try:
            await client.send("Captcha.waitForSolve", {"detectTimeout": 10 * 1000})
        except Exception as e:
            self.logger.error(f"Error waiting for captcha solve: {str(e)}")
            raise CaptchaError(str(e))

    async def _handle_input_or_button(
        self, page: Page, action: Dict[str, Any], user_service: UserService
    ) -> Optional[int]:
        """
        Handle input fields and button interactions.

        Args:
            page: Playwright page object
            action: Action configuration
            user_service: User service information

        Returns:
            Optional[int]: Updated customer number index for input fields
        """
        selector = get_selector(action)
        customer_number_index = 0

        try:
            if action["element_type"] == "input":
                size = int(action.get("size", len(user_service.customer_number)))
                input_value = user_service.customer_number[
                    customer_number_index : customer_number_index + size
                ]
                await page.fill(selector, input_value)
                return customer_number_index + size

            elif action["element_type"] == "button":
                await page.click(selector)
                return customer_number_index

        except Exception as e:
            self.logger.error(f"Error handling input/button: {str(e)}")
            raise ScrapingError(f"Input/Button handling failed: {str(e)}")

    async def _handle_modal(self, page: Page, selector: str) -> None:
        """Handle modal dialogs."""
        try:
            await page.wait_for_selector(selector)
            await page.click(selector)
        except Exception as e:
            self.logger.warning(f"Modal handling failed: {str(e)}")

    async def _execute_action(
        self, page: Page, action: Dict[str, Any], user_service: UserService
    ) -> List[Dict[str, Any]]:
        """
        Execute a single scraping action.

        Args:
            page: Playwright page object
            action: Action configuration
            user_service: User service information

        Returns:
            List of extracted data
        """
        try:
            element_type = action["element_type"]
            selector = get_selector(action)

            await page.wait_for_selector(selector, timeout=5000)

            if element_type in ["input", "button"]:
                await self._handle_input_or_button(page, action, user_service)
                return []
            elif element_type == "buttons":
                await self._handle_buttons(page, selector)
                return self.bills
            elif element_type in [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "p",
                "div",
                "span",
                "table",
                "tbody",
                "td",
                "a",
                "ul",
                "name",
            ]:
                return await self._handle_element(page, action, user_service)
            elif element_type == "modal":
                await self._handle_modal(page, selector)
                return []

            return []

        except Exception as e:
            self.logger.error(f"Action execution failed: {str(e)}")
            raise ScrapingError(f"Action execution failed: {str(e)}")

    def _prepare_response(self, save_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the final response object.

        Args:
            save_result: Result from saving bills

        Returns:
            Dict containing debt status, save results, and extraction flags
        """
        return {
            "debt": self.debt,
            "save_result": save_result,
            "should_extract": (
                save_result.get("new_bills_saved", False)
                or not save_result.get("success", False)
                or any("url" in bill for bill in self.bills)
            ),
        }

    async def _process_and_save_results(
        self, result: List[Dict[str, Any]], user_service_id: str
    ) -> Dict[str, Any]:
        """
        Process and save the scraped results.

        Args:
            result: List of scraped data
            user_service_id: User service identifier

        Returns:
            Dict containing save operation results
        """
        try:
            self.logger.info(f"Processing results for user service: {user_service_id}")
            self.logger.info(f"Extracted data: {result}")
            return await self.bill_service.save_bills(
                user_service_id=user_service_id, bills=result, debt=self.debt
            )
        except Exception as e:
            self.logger.error(f"Error saving bills: {str(e)}")
            return {
                "success": False,
                "message": f"Error saving bills: {str(e)}",
                "new_bills_saved": False,
            }

    async def _handle_scraping(
        self,
        page_result: Tuple[Page, Any],
        config: ScrapingConfig,
        user_service: UserService,
    ) -> List[Dict[str, Any]]:
        """
        Handle the main scraping logic with proper error handling and retries.

        Args:
            page_result: Tuple containing page and client objects
            config: Scraping configuration
            user_service: User service information

        Returns:
            List of scraped data

        Raises:
            ScrapingError: If scraping operation fails
        """
        page, client = page_result
        consecutive_errors = 0
        customer_number_index = 0

        try:
            # Set up event handlers
            page.on("dialog", self._handle_dialog)
            page.on("download", self._handle_download)

            # Handle captcha if needed
            if config.captcha:
                await self._handle_captcha(page, client, config, user_service)

            # Execute scraping sequence
            for action in config.sequence:
                try:
                    self.logger.info(f"Executing action: {action}")
                    result = await self._execute_action(
                        page=page, action=action, user_service=user_service
                    )

                    if result:
                        self.bills.extend(result)

                    consecutive_errors = 0

                except Exception as e:
                    self.logger.warning(f"Action execution failed: {str(e)}")
                    consecutive_errors += 1

                    # Restart scraping after multiple consecutive errors
                    if consecutive_errors >= 4:
                        self.logger.error("Too many consecutive errors, restarting...")
                        raise ScrapingError("Multiple consecutive failures")

                    continue

            return self.bills

        except Exception as e:
            self.logger.error(f"Scraping operation failed: {str(e)}")
            raise ScrapingError(f"Scraping operation failed: {str(e)}")
        finally:
            await page.close()

    async def _handle_captcha(
        self, page, client, config: ScrapingConfig, user_service: UserService
    ):
        """Handle captcha solving with improved error handling"""
        try:
            if config.captcha_sequence:
                await self._solve_captcha_with_sequence(page, config, user_service)
            else:
                await self._wait_for_captcha_solve(client)
        except Exception as e:
            self.logger.error(f"Captcha handling failed: {str(e)}")
            raise CaptchaError(f"Captcha handling failed: {str(e)}")

    async def _handle_element(
        self, page: Page, action: Dict[str, Any], user_service: UserService
    ) -> List[Dict[str, Any]]:
        """
        Handle element actions and debt checking with improved error handling.

        Args:
            page: Playwright page object
            action: Action configuration
            user_service: User service information

        Returns:
            List of extracted data

        Raises:
            ScrapingError: If element handling fails
        """
        try:
            selector = get_selector(action)
            elements = await page.query_selector_all(selector)

            # Handle debt check if specified
            if action.get("debt"):
                await self._check_debt_status(elements, action.get("no_debt_text"))

            # Handle query if present
            if action.get("query"):
                results = await self._handle_query(
                    page=page,
                    action=action,
                    elements=elements,
                    user_service_id=user_service.id,
                )
                return results

            return []

        except Exception as e:
            self.logger.error(f"Element handling failed: {str(e)}")
            raise ScrapingError(f"Element handling failed: {str(e)}")

    async def _check_debt_status(
        self, elements: List[Any], no_debt_text: Optional[str]
    ) -> None:
        """
        Check debt status based on element text.

        Args:
            elements: List of page elements
            no_debt_text: Regular expression pattern for no debt condition
        """
        try:
            if elements:
                debt_message = await elements[0].inner_text()
                if no_debt_text and re.search(no_debt_text, debt_message):
                    self.debt = False
                else:
                    self.debt = True
            else:
                self.debt = True

        except Exception as e:
            self.logger.error(f"Error checking debt status: {str(e)}")
            self.debt = True  # Default to debt on error

    async def _handle_query(
        self,
        page: Page,
        action: Dict[str, Any],
        elements: List[Any],
        user_service_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Handle query actions for elements with improved URL handling.

        Args:
            page: Playwright page object
            action: Action configuration
            elements: List of page elements
            user_service_id: User service identifier

        Returns:
            List of extracted data

        Raises:
            ScrapingError: If query handling fails
        """
        try:
            if action.get("redirect"):
                return await self._handle_redirect(page, elements[0])
            elif action.get("form"):
                return await self._handle_form_submission(elements)
            else:
                return await self._handle_urls(page, elements, user_service_id)

        except Exception as e:
            self.logger.error(f"Query handling failed: {str(e)}")
            raise ScrapingError(f"Query handling failed: {str(e)}")

    async def _handle_redirect(self, page: Page, element: Any) -> List[Dict[str, Any]]:
        """Handle redirect actions."""
        href = await element.get_attribute("href")
        absolute_url = urljoin(page.url, href)
        await page.goto(absolute_url, wait_until="load")
        return []

    async def _handle_form_submission(
        self, elements: List[Any]
    ) -> List[Dict[str, Any]]:
        """Handle form submission actions."""
        for i in range(0, 6, 2):
            try:
                td = elements[i]
                form = await td.query_selector("form")
                await form.dispatch_event("submit")
                await asyncio.sleep(12)
            except Exception as e:
                self.logger.warning(f"Form submission failed: {str(e)}")
        return []

    async def _handle_urls(
        self, page: Page, elements: List[Any], user_service_id: str
    ) -> List[Dict[str, Any]]:
        """Handle URL extraction and processing."""
        try:
            # Extract URLs from elements
            elements_href = [
                await element.get_attribute("href") for element in elements
            ]

            # Clean and format URLs
            base_url = urlunparse(urlparse(page.url)._replace(path=""))
            elements_formatted = [
                {"url": urljoin(base_url, href)}
                for href in elements_href
                if href is not None
            ]

            # Save bills if needed
            if elements_formatted:
                self.bills.extend(elements_formatted)
                if not self.save_bills_called:
                    await self.bill_service.save_bills(
                        user_service_id=user_service_id,
                        bills=elements_formatted,
                        debt=self.debt,
                    )
                    self.save_bills_called = True

            return elements_formatted

        except Exception as e:
            self.logger.error(f"URL handling failed: {str(e)}")
            return []

    async def _handle_buttons(self, page: Page, selector: str) -> None:
        """
        Handle button clicking and file downloading with improved error handling.

        Args:
            page: Playwright page object
            selector: Button selector

        Raises:
            ScrapingError: If button handling fails
        """
        try:
            buttons = await page.query_selector_all(selector)
            self.logger.info(f"Found {len(buttons)} buttons to process")

            for button in buttons:
                try:
                    # Ensure button is visible
                    await button.scroll_into_view_if_needed()

                    # Set up download handler
                    async with page.expect_download(timeout=30000) as download_info:
                        await button.click()

                    # Wait for download and process
                    download = await download_info.value
                    await self._handle_download(download)

                    # Add delay between clicks
                    await asyncio.sleep(2)

                except Exception as e:
                    self.logger.error(f"Error processing button: {str(e)}")
                    continue

        except Exception as e:
            self.logger.error(f"Button handling failed: {str(e)}")
            raise ScrapingError(f"Button handling failed: {str(e)}")
