import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from decimal import Decimal
import pdfplumber


@dataclass
class Address:
    street: Optional[str] = None
    number: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None


class GenericBillParser:
    def __init__(self):
        # Dictionary to store all patterns
        self.patterns = {
            # Basic information patterns
            "date": [
                r"Fecha(?:\sde)?\semisión:\s*(\d{2}/\d{2}/\d{2,4})",
                r"Fecha:\s*(\d{2}/\d{2}/\d{2,4})",
                r"Emisión:\s*(\d{2}/\d{2}/\d{2,4})",
                r"FECHA DE EMISIÓN\s*(\d{2}/\d{2}/\d{2,4})",
            ],
            "account_number": [
                r"NÚMERO DE CUENTA:\s*(\d+)",
                r"CÓDIGO PAGO ELECTRÓNICO\s*(\d+)",
                r"Cod\.\s*018\s*(\d+)",
                r"N° de Cliente:\s*(\d+)",
                r"(?:Cuenta|Account)(?:\sNº)?:\s*(\d+)",
                r"N° DE CLIENTE\s*(\d+)",
                r"Nº\s*(\d{3}-\d{7}-\d{3}-\d)",
                r"Código de LINK PAGOS / BANELCO:\s*(\d+)",
            ],
            "customer_name": [
                r"(?:NOMBRE:|Cliente:)\s*([\w\s,]+?)(?=\n)",
                r"(?<=\n)((?!CÓDIGO PAGO ELECTRÓNICO)[\w\s]+?)(?=\nCL\s)",
                r"Titular:\s*([\w\s,]+?)(?=\n)",
                r"APELLIDO Y NOMBRE[^:]*?:\s*([\w\s,]+?)(?=\n)",
                r"^([A-Z\s,]+?)(?=\s+Vencimiento)",
            ],
            "due_date": [
                r"Vencimiento actual:\s*(\d{2}/\d{2}/\d{2,4})",
                r"Vencimiento:\s*(\d{2}/\d{2}/\d{2,4})",
                r"C\.E\.S\.P\..*?:\s*(\d{2}/\d{2}/\d{2,4})",
                r"Fecha de vencimiento:\s*(\d{2}/\d{2}/\d{2,4})",
                r"VENCIMIENTO\s*(\d{2}/\d{2}/\d{2,4})",
            ],
            "total_amount": [
                r"TOTAL\s*\$\s*([\d,.]+)",
                r"Total a pagar.*?\$\s*([\d,.]+)",
                r"Importe Total:?\s*\$\s*([\d,.]+)",
                r"TOTAL PESOS:\s*\$\s*([\d,.]+)",
                r"IMPORTE A PAGAR\s*\$\s*([\d,.]+)",
                r"\$\s*([\d,.]+)(?=\s*$)",
            ],
            # Business information
            "business_info": [
                r"CUIT[^:]*?:\s*([\d-]+)",
                r"INGRESOS BRUTOS:\s*(\d+)",
                r"IVA\s*([^:\n]+?)(?=\n)",
                r"Inicio[^:]*?:\s*(\d{2}/\d{2}/\d{4})",
                r"ESTABLECIMIENTO[^:]*?:\s*([\d-]+)",
            ],
            # Service period
            "service_period": [
                r"PERIODO\s+([^$\n]+?)(?=\s+VENCIMIENTO)",
                r"Período Facturado:\s*([\w\s/]+)",
                r"(\d{2}/\d{2}/\d{2,4})\s*al\s*(\d{2}/\d{2}/\d{2,4})",
            ],
            # Address patterns
            "address": [
                r"Domicilio:\s*(.*?)(?=\n)",
                r"DOMICILIO POSTAL\s*(?:Calle)?\s*(.*?)(?=\n)",
                r"Domicilio suministro:\s*(?:CL\s+)?(.*?)(?=\d{4})",
                r"(?:CL|Calle)\s+(.*?)(?=\d{4})",
                r"Dirección de suministro:\s*(.*?)(?=\n)",
            ],
            "postal_code": [
                r"(?:CL|Domicilio).*?(\d{4})\s+([A-Z\s]+)",
                r"C\.P\.:\s*(\d{4})",
                r"CP:\s*(\d{4})",
            ],
            "location": [
                r"(?:CL|Domicilio).*?\d{4}\s+([A-Z\s]+(?:SAN RAFAEL|MENDOZA|BUENOS AIRES)[A-Z\s]+)",
                r"Localidad:\s*([A-Z\s]+)",
                r"Loc\.:\s*([A-Z\s]+)",
            ],
            # Charges and services
            "charges": [
                r"(Cargo Fijo[^$]*?)\$\s*([\d,.]+)",
                r"(Cargo Variable[^$]*?)\$\s*([\d,.]+)",
                r"(Subsidio[^:]*?):\s*\$?\s*(-?[\d,.]+)",
                r"(Impuesto[^:]*?):\s*\$?\s*([\d,.]+)",
                r"(Cargo[^:]*?):\s*\$?\s*([\d,.]+)",
                r"(Bonificación[^:]*?):\s*\$?\s*(-?[\d,.]+)",
                r"(Cuota Fija[^$]*?)\$?\s*([\d,.]+)",
                r"([\w\s]+?)\s*\$\s*([\d,.]+)(?=\n)",
            ],
            # Service details
            "service_details": [
                r"(\d{2}/\d{4})\s+(\d+)\s+([A-Z\s]+)\s+(\d+\s*[A-Z]+)\s+\$\s*([\d,.]+)",
                r"FTTH\s+([^$\n]+?)(?=\s+\$)",
                r"Internet\s+(\d+\s*MB)",
            ],
            # Additional identifiers
            "invoice_number": [
                r"FACTURA\s+([A-Z]\s+[\d-]+)",
                r"B-(\d+)",
                r"Nº\s*(\d{3}-\d{7}-\d{3}-\d)",
            ],
            # Payment installments
            "installments": [
                r"CUOTA\s+\d+\s+VENCIMIENTO\s+(\d{2}/\d{2}/\d{4})\s+IMPORTE\s+\$\s*([\d,.]+)"
            ],
        }

    def add_pattern(self, category: str, pattern: str) -> None:
        """Add a new pattern to an existing category or create a new category."""
        if category in self.patterns:
            self.patterns[category].append(pattern)
        else:
            self.patterns[category] = [pattern]

    def extract_field(self, text: str, patterns: List[str], default: Any = None) -> Any:
        """Extract a field using multiple regex patterns."""
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            except (AttributeError, IndexError):
                continue
        return default

    def extract_charges(self, text: str) -> Dict[str, Decimal]:
        """Extract all charges from the bill."""
        charges = {}
        for pattern in self.patterns["charges"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                concept = match.group(1).strip()
                amount = Decimal(match.group(2).replace(",", "."))
                charges[concept] = amount
        return charges

    def extract_business_info(self, text: str) -> Dict[str, str]:
        """Extract business information."""
        info = {}
        for field in [
            "CUIT",
            "INGRESOS BRUTOS",
            "IVA",
            "INICIO ACTIVIDAD",
            "ESTABLECIMIENTO",
        ]:
            value = self.extract_field(text, self.patterns["business_info"])
            if value:
                info[field] = value
        return info

    def extract_installments(self, text: str) -> List[Dict[str, Any]]:
        """Extract payment installments if available."""
        installments = []
        for pattern in self.patterns["installments"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                installments.append(
                    {
                        "due_date": match.group(1),
                        "amount": Decimal(match.group(2).replace(",", ".")),
                    }
                )
        return installments

    def extract_service_details(self, text: str) -> List[Dict[str, Any]]:
        """Extract service details."""
        details = []
        for pattern in self.patterns["service_details"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    details.append(
                        {
                            "service": match.group(1),
                            "description": " ".join(match.groups()[1:]),
                        }
                    )
                else:
                    details.append({"description": match.group(1)})
        return details

    def extract_address(self, text: str) -> Address:
        """Extract address information."""
        address = Address()

        # Extract street and number
        street_match = self.extract_field(text, self.patterns["address"])
        if street_match:
            parts = street_match.split()
            address.street = " ".join(parts[:-1]) if len(parts) > 1 else street_match
            address.number = parts[-1] if len(parts) > 1 else None

        # Extract location information
        address.postal_code = self.extract_field(text, self.patterns["postal_code"])
        location_match = self.extract_field(text, self.patterns["location"])
        if location_match:
            address.city = next(
                (
                    part
                    for part in location_match.split()
                    if part in ["SAN RAFAEL", "MENDOZA", "MALARGUE", "BUENOS AIRES"]
                ),
                None,
            )
            if address.city:
                address.province = (
                    "MENDOZA"
                    if address.city in ["SAN RAFAEL", "MALARGUE"]
                    else address.city
                )

        # Extract apartment information
        apt_match = re.search(r"Dpto:(\d{2}-\d{2})", text)
        if apt_match:
            address.apartment = apt_match.group(1)

        return address

    def extract_consumption_history(self, text: str) -> Dict[str, float]:
        """Extract consumption history."""
        history = {}
        history_pattern = r"(\d{2}/\d{2})\s+(\d+(?:,\d+)?)"
        matches = re.finditer(history_pattern, text)

        for match in matches:
            period = match.group(1)
            consumption = float(match.group(2).replace(",", "."))
            history[period] = consumption

        return history

    def extract_address(self, text: str) -> Address:
        """Extract address information."""
        address = Address()

        # Extract street and number
        street_match = self.extract_field(text, self.patterns["address"])
        if street_match:
            parts = street_match.split()
            address.street = " ".join(parts[:-1]) if len(parts) > 1 else street_match
            address.number = parts[-1] if len(parts) > 1 else None

        # Extract floor and apartment
        floor_apt_match = re.search(r"(?:P(\d+))?\s*(?:D(\d+))?", text)
        if floor_apt_match:
            address.floor = floor_apt_match.group(1)
            address.apartment = floor_apt_match.group(2)

        # Extract postal code and location
        address.postal_code = self.extract_field(text, self.patterns["postal_code"])
        location_match = self.extract_field(text, self.patterns["location"])
        if location_match:
            parts = location_match.split()
            address.city = next(
                (
                    part
                    for part in parts
                    if part in ["SAN RAFAEL", "MENDOZA", "BUENOS AIRES"]
                ),
                None,
            )
            address.province = parts[-1] if len(parts) > 1 else None

        return address

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse all relevant information from the bill text."""
        data = {
            "invoice_number": self.extract_field(text, self.patterns["invoice_number"]),
            "invoice_date": self.extract_field(text, self.patterns["date"]),
            "account_number": self.extract_field(text, self.patterns["account_number"]),
            "customer_name": self.extract_field(text, self.patterns["customer_name"]),
            "due_date": self.extract_field(text, self.patterns["due_date"]),
            "total_amount": self.extract_field(text, self.patterns["total_amount"]),
            "service_period": self.extract_field(text, self.patterns["service_period"]),
            "address": self.extract_address(text).__dict__,
            "business_info": self.extract_business_info(text),
            "charges": self.extract_charges(text),
            "service_details": self.extract_service_details(text),
            "installments": self.extract_installments(text),
        }

        return {k: v for k, v in data.items() if v is not None and v != {} and v != ""}


def process_utility_bill_pdf(pdf_path: str) -> Dict[str, Any]:
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


def main():
    """Main function to demonstrate usage."""
    try:
        pdf_path = "/home/j0k3r/home/Facultad/ss-webscraping-ms/fac_ay.pdf"
        data = process_utility_bill_pdf(pdf_path)

        print("\n=== Bill Information ===")
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"\n{key.title()}:")
                for subkey, subvalue in value.items():
                    print(f"  {subkey}: {subvalue}")
            else:
                print(f"{key.title()}: {value}")

    except Exception as e:
        print(f"Error in main execution: {str(e)}")


if __name__ == "__main__":
    main()
