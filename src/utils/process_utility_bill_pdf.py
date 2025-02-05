from typing import Any, Dict
import pdfplumber

from src.utils.convert_data import GenericBillParser


async def process_utility_bill_pdf(pdf_path: str) -> Dict[str, Any]:
    """Process a utility bill PDF and return structured data."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(
                page.extract_text() for page in pdf.pages if page.extract_text()
            )

        parser = GenericBillParser()
        return parser.parse(text)
    except Exception as e:
        print(f"Error processing utility bill PDF: {str(e)}")
        return {}
