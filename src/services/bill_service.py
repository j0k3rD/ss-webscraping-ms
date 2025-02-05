import os, tempfile, asyncio, logging
from typing import List, Dict, Optional
import httpx
from src.core.errors import HTTPClientError
from src.services.http_client import MainServiceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BillService:
    """Service for handling bill-related operations."""

    def __init__(self):
        self.client = MainServiceClient()

    async def save_bills(
        self, user_service_id: int, bills: List[Dict], debt: bool = False
    ) -> Dict:
        """
        Save bills for a user service.

        Args:
            user_service_id: ID of the user service
            bills: List of bill data to save
            debt: Whether the bills represent debt

        Returns:
            Dict containing operation status and results
        """
        try:
            # Verify user service exists
            user_service = await self.client.get_user_service(user_service_id)
            if not user_service:
                logger.error(f"User service {user_service_id} not found")
                return {
                    "success": False,
                    "message": "User service not found",
                    "new_bills_saved": False,
                }

            try:
                # Get existing scrapped data
                scrapped_data = await self.client.get_scrapped_data(user_service_id)
            except HTTPClientError as e:
                # If 404, create new scrapped data
                if e.status_code == 404:
                    logger.info(
                        f"No existing scrapped data found for user service {user_service_id}. Creating new entry."
                    )
                    result = await self.client.create_scrapped_data(
                        user_service_id=user_service_id, bills=bills, debt=debt
                    )
                    return {
                        "success": True,
                        "message": "New scrapped data created with bills",
                        "new_bills_saved": True,
                    }
                else:
                    # Re-raise if it's not a 404 error
                    raise

            # Handle existing scrapped data
            if isinstance(scrapped_data, dict):
                scrapped_data = [scrapped_data]

            new_bills_saved = False
            for data in scrapped_data:
                if not isinstance(data, dict):
                    logger.warning(f"Invalid scrapped data format: {data}")
                    continue

                # Update existing scrapped data
                current_bills = data.get("bills_url", [])
                if not isinstance(current_bills, list):
                    current_bills = []

                # Create a set of existing URLs to avoid duplicates
                existing_urls = {
                    bill.get("url") for bill in current_bills if bill.get("url")
                }

                # Only add bills that don't already exist
                new_bills = [
                    bill
                    for bill in bills
                    if bill.get("url") and bill["url"] not in existing_urls
                ]

                if new_bills:
                    updated_bills = current_bills + new_bills
                    result = await self.client.update_scrapped_data(
                        scrapped_data_id=data["id"], bills=updated_bills, debt=debt
                    )
                    if result:
                        new_bills_saved = True

            return {
                "success": True,
                "message": "Bills processed successfully",
                "new_bills_saved": new_bills_saved,
            }

        except Exception as e:
            logger.error(f"Error saving bills: {str(e)}")
            return {
                "success": False,
                "message": f"Error saving bills: {str(e)}",
                "new_bills_saved": False,
            }

    async def download_pdfs(self, bills: List[Dict]) -> List[str]:
        """
        Download PDFs from bill URLs in parallel.

        Args:
            bills: List of bill data containing URLs

        Returns:
            List of paths to downloaded PDF files
        """
        if not isinstance(bills, list):
            logger.error(f"Invalid bills format: {type(bills)}")
            return []

        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")

        valid_bills = [bill for bill in bills if bill.get("url")]
        if not valid_bills:
            logger.warning("No valid URLs found in bills")
            return []

        async with httpx.AsyncClient() as client:
            tasks = [
                self._download_single_pdf(client, bill["url"], temp_dir, i)
                for i, bill in enumerate(valid_bills, start=1)
            ]

            downloaded_files = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out errors and None values
            valid_files = [
                f for f in downloaded_files if f is not None and isinstance(f, str)
            ]

            logger.info(f"Successfully downloaded {len(valid_files)} PDFs")
            return valid_files

    async def _download_single_pdf(
        self, client: httpx.AsyncClient, url: str, temp_dir: str, index: int
    ) -> Optional[str]:
        """
        Download a single PDF file.

        Args:
            client: HTTP client
            url: URL to download from
            temp_dir: Directory to save the file
            index: File index for naming

        Returns:
            Path to downloaded file or None if download failed
        """
        try:
            logger.info(f"Downloading PDF from {url}")
            response = await client.get(url)
            response.raise_for_status()

            file_path = os.path.join(temp_dir, f"{index}.pdf")
            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Successfully downloaded PDF to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to download PDF from {url}: {str(e)}")
            return None
