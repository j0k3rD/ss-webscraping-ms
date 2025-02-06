import json
import os, logging
from typing import List, Dict, Any, Optional
from src.services.http_client import MainServiceClient
from src.services.bill_service import BillService
from src.utils.process_utility_bill_pdf import process_utility_bill_pdf
from src.utils.convert_data import GenericBillParser, convert_data_to_json
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtractDataService:
    """Service for extracting and processing bill data."""

    def __init__(self):
        self.client = MainServiceClient()
        self.bill_service = BillService()
        self.processed_data: List[Dict] = []

    async def process_bills(self, user_service_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process bills for a given user service.
        """
        try:
            user_service_id = user_service_data["user_service"]["id"]
            logger.info(f"Starting bill processing for user service {user_service_id}")

            # Get scrapped data
            scrapped_data = await self.client.get_scrapped_data(user_service_id)
            if not scrapped_data:
                logger.error(
                    f"No scrapped data found for user service {user_service_id}"
                )
                return {"success": False, "message": "No scrapped data found"}

            # Check if scrapped_data is a dictionary and has bills_url
            if isinstance(scrapped_data, dict):
                bills = scrapped_data.get("bills_url", [])
            else:
                # If scrapped_data is already a list of bills
                bills = scrapped_data

            # Process bills
            await self._process_all_bills(bills)

            # Save processed data
            if self.processed_data:
                save_result = await self._save_processed_data(user_service_id)
                return {
                    "success": True,
                    "message": "Bills processed and saved successfully",
                    "data": save_result,
                }

            return {"success": True, "message": "No new bills to process", "data": None}

        except Exception as e:
            error_msg = f"Error processing bills: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    async def _process_all_bills(self, bills: List[Dict]) -> None:
        """
        Process both URL-based and content-based bills.
        """
        if not isinstance(bills, list):
            logger.error(f"Invalid bills format: {type(bills)}")
            return

        # Separate bills by type
        url_bills = []
        content_bills = []

        for bill in bills:
            if not isinstance(bill, dict):
                continue

            # Handle nested bills_url structure
            if "bills_url" in bill and isinstance(bill["bills_url"], list):
                for bill_url in bill["bills_url"]:
                    if bill_url.get("url"):
                        url_bills.append(bill_url)
                    elif bill_url.get("content"):
                        content_bills.append(bill_url)

        # Process URL-based bills
        if url_bills:
            await self._process_url_bills(url_bills)

        # Process content-based bills
        if content_bills:
            await self._process_content_bills(content_bills)

    async def _process_url_bills(self, url_bills: List[Dict]) -> None:
        """
        Process bills that need to be downloaded from URLs.

        Args:
            url_bills: List of bills containing URLs
        """
        try:
            # Download PDFs
            pdf_files = await self.bill_service.download_pdfs(url_bills)
            logger.info(f"Downloaded {len(pdf_files)} PDF files")

            # Process each PDF
            for pdf_path in pdf_files:
                logger.info(f"Processing PDF: {pdf_path}")
                extracted_data = await self._process_pdf(pdf_path)
                if extracted_data:
                    logger.info(f"Extracted data from PDF: {extracted_data}")
                    try:
                        json_data = await self._convert_to_json(extracted_data)
                        self.processed_data.append(json_data)
                    except Exception as e:
                        logger.error(
                            f"Failed to process data from {pdf_path}: {str(e)}"
                        )
                        continue
                else:
                    logger.warning(f"No data extracted from PDF: {pdf_path}")

                # Clean up the temporary file
                try:
                    os.remove(pdf_path)
                    logger.info(f"Removed temporary file: {pdf_path}")
                except Exception as e:
                    logger.warning(
                        f"Failed to remove temporary file {pdf_path}: {str(e)}"
                    )

        except Exception as e:
            logger.error(f"Error processing URL bills: {str(e)}")

    async def _process_content_bills(self, content_bills: List[Dict]) -> None:
        """Process bills that already have content."""
        logger.info(f"Processing {len(content_bills)} content-based bills")
        for bill in content_bills:
            try:
                content = bill.get("content", {})

                # Handle both string and dict content
                if isinstance(content, dict):
                    content = content.get("content", "")

                if not isinstance(content, str):
                    logger.error(f"Invalid content type: {type(content)}")
                    continue

                bill_data = {
                    "content": content,
                    "url": bill.get("url"),
                    "type": "content",
                }

                json_data = await convert_data_to_json(content)  # Pass content directly
                self.processed_data.append(json_data)

            except Exception as e:
                logger.error(f"Error processing content bill: {str(e)}")
                continue

    async def _process_pdf(self, pdf_path: str) -> Optional[Dict]:
        """
        Process a single PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted data from the PDF or None if processing fails
        """
        try:

            return await process_utility_bill_pdf(pdf_path)
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return None

    async def _convert_to_json(self, data: dict) -> dict:
        """
        Convert extracted data to JSON format.

        Args:
            data: Dictionary containing extracted data

        Returns:
            dict: JSON-compatible dictionary
        """
        try:
            # Convert Decimal objects to strings
            def decimal_to_str(obj):
                if isinstance(obj, Decimal):
                    return str(obj)
                return obj

            # Clean and convert the dictionary
            cleaned_data = json.loads(json.dumps(data, default=decimal_to_str))
            return cleaned_data

        except Exception as e:
            logger.error(f"Error converting data to JSON: {str(e)}")
            raise

    async def _save_processed_data(self, user_service_id: int) -> str:
        """
        Save processed data to the backend.

        Args:
            user_service_id: ID of the user service

        Returns:
            Status message indicating save result
        """
        try:
            # Convert Decimal objects to strings in the processed data
            def convert_decimals(obj):
                if isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(i) for i in obj]
                elif isinstance(obj, Decimal):
                    return str(obj)
                return obj

            # Convert list to dictionary and handle Decimal serialization
            data_to_save = convert_decimals(
                {i: data for i, data in enumerate(self.processed_data)}
                if isinstance(self.processed_data, list)
                else self.processed_data
            )

            scrapped_data = await self.client.get_scrapped_data(user_service_id)
            if not scrapped_data:
                raise ValueError("No scrapped data found")

            # Handle case where scrapped_data is a list
            if isinstance(scrapped_data, list):
                if not scrapped_data:
                    raise ValueError("Empty scrapped data list")
                scrapped_data = scrapped_data[0]  # Take first item if list

            # Verify scrapped_data is a dict before accessing
            if not isinstance(scrapped_data, dict):
                raise ValueError(f"Invalid scrapped data format: {type(scrapped_data)}")

            scrapped_data_id = scrapped_data.get("id")
            if not scrapped_data_id:
                raise ValueError("Scrapped data ID not found")

            result = await self.client.update_scrapped_data(
                scrapped_data_id=scrapped_data_id, consumption_data=data_to_save
            )

            return "Data saved successfully" if result else "Failed to save data"

        except Exception as e:
            error_msg = f"Error saving processed data: {str(e)}"
            logger.error(error_msg)
            raise
