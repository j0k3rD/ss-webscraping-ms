import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from decimal import Decimal, DecimalException
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
            "meter_info": [
                r"Nro medidor:\s*(\d+)",
                r"Lectura Actual.*?(\d+)\s+Real\s+(\d{2}/\d{2}/\d{4})",
                r"Lectura Anterior.*?(\d+)\s+(\d{2}/\d{2}/\d{4})",
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
            "consumption": [
                r"Consumo Medido\s+(\d+)\s*m³",
                r"Factor de correción.*?\(1\)\s+(\d+\.\d+)",
                r"Calorías suministradas\s+(\d+\.\d+)\s*kcal",
                r"Consumo a facturar a \d+ kcal/m³\s+(\d+)\s*x\s+(\d+\.\d+)\s*x\s*\(\s*(\d+\.\d+)\s*\)\s+(\d+)\s*m³",
                r"M3 asignados.*?(\d+\.\d+)\s*m³",
                r"Cargo Variable kWh\s+(\d+)\s+([\d,.]+)\s+([\d,.]+)",
            ],
        }

    def safe_decimal_convert(self, value: str) -> Decimal:
        """Safely convert a string to Decimal, handling different number formats."""
        if not value:
            return Decimal("0")

        # Remove any spaces
        value = value.strip()

        # Handle numbers with both comma and period
        if "," in value and "." in value:
            # Assuming format like "1.234,56" -> convert to "1234.56"
            value = value.replace(".", "").replace(",", ".")
        # Handle numbers with only comma
        elif "," in value:
            value = value.replace(",", ".")

        try:
            return Decimal(value)
        except (DecimalException, ValueError):
            return Decimal("0")

    def extract_consumption(self, text: str) -> Dict[str, Decimal]:
        """Extract consumption information with safe decimal conversion."""
        measured = self.safe_decimal_convert(
            self.extract_field(text, [self.patterns["consumption"][0]]) or "0"
        )
        factor = self.safe_decimal_convert(
            self.extract_field(text, [self.patterns["consumption"][1]]) or "0"
        )
        calories = self.safe_decimal_convert(
            self.extract_field(text, [self.patterns["consumption"][2]]) or "0"
        )

        consumption_match = re.search(self.patterns["consumption"][3], text)
        if consumption_match:
            billed = self.safe_decimal_convert(consumption_match.group(4))
        else:
            billed = Decimal("0")

        assigned = self.safe_decimal_convert(
            self.extract_field(text, [self.patterns["consumption"][4]]) or "0"
        )

        variable_charge_match = re.search(self.patterns["consumption"][5], text)
        variable_charge = {
            "kwh": Decimal("0"),
            "rate": Decimal("0"),
            "amount": Decimal("0"),
        }

        if variable_charge_match:
            variable_charge = {
                "kwh": self.safe_decimal_convert(variable_charge_match.group(1)),
                "rate": self.safe_decimal_convert(variable_charge_match.group(2)),
                "amount": self.safe_decimal_convert(variable_charge_match.group(3)),
            }

        return dict(
            measured_m3=measured,
            correction_factor=factor,
            calories_supplied=calories,
            billed_m3=billed,
            assigned_m3=assigned,
            variable_charge=variable_charge,
        )

    def add_pattern(self, category: str, pattern: str) -> None:
        """Add a new pattern to an existing category or create a new category."""
        if category in self.patterns:
            self.patterns[category].append(pattern)
        else:
            self.patterns[category] = [pattern]

    def extract_meter_info(self, text: str) -> Dict[str, Any]:
        """Extract meter reading information."""
        meter_info = {}
        meter_match = re.search(self.patterns["meter_info"][0], text)
        if meter_match:
            meter_info["meter_number"] = meter_match.group(1)

        reading_match = re.search(self.patterns["meter_info"][1], text)
        if reading_match:
            meter_info.update(
                {
                    "current_reading": {
                        "date": reading_match.group(2),
                        "value": reading_match.group(3),
                        "type": reading_match.group(4),
                    },
                    "previous_reading": {
                        "date": reading_match.group(5),
                        "value": reading_match.group(6),
                    },
                    "consumption": reading_match.group(7),
                }
            )
        return meter_info

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

    def extract_business_info(self, text: str) -> Dict[str, str]:
        """Extract business information."""
        info = {}
        for field in ["CUIT", "INGRESOS BRUTOS"]:
            try:
                pattern = self.patterns.get(field)
                if pattern:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match and match.groups():
                        info[field] = match.group(1).strip()
            except (re.error, IndexError, AttributeError):
                continue
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
            "service_details": self.extract_service_details(text),
            "installments": self.extract_installments(text),
            "meter_info": self.extract_meter_info(text),
            "consumption": self.extract_consumption(text),
        }

        return {k: v for k, v in data.items() if v is not None and v != {} and v != ""}


def process_utility_bill_pdf(pdf_path: str) -> Dict[str, Any]:
    """Process a utility bill PDF and return structured data."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(
                page.extract_text() for page in pdf.pages if page.extract_text()
            )

        # print(text)
        parser = GenericBillParser()
        return parser.parse(text)
    except Exception as e:
        print(f"Error processing utility bill PDF: {str(e)}")
        return {}


def main():
    """Main function to demonstrate usage."""
    try:
        pdf_path = "/home/j0k3r/home/Facultad/ss-webscraping-ms/fa.pdf"
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
