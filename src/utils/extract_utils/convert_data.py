import datetime
import re

# Regex patterns for extracting dates
date_regex = [
    re.compile(r"Vto.:\s(\d{2}/\d{2}/\d{4})"),
    re.compile(r"PERIODO\s(\d{2}/\d{2}/\d{2})"),
    re.compile(r"Fecha:\s?(\d{2}/\d{2}/\d{2})"),
    re.compile(r"Vto.:\s?(\d{2}/\d{2}/\d{4})"),
    re.compile(r"al:\s?(\d{2}/\d{2}/\d{4})"),
    re.compile(r"Fecha emisión:\s(\d{2}/\d{2}/\d{4})"),  # Fecha de emisión
    re.compile(
        r"Fecha Vto\. C\.E\.S\.P\.:\s(\d{2}/\d{2}/\d{4})"
    ),  # Fecha de vencimiento
    re.compile(r"Próximo Vencimiento:\s(\d{2}/\d{2}/\d{4})"),  # Próximo vencimiento
]

# Regex patterns for extracting addresses
address_regex = [
    re.compile(r"DOMICILIO POSTAL\n(.+?)\n"),
    re.compile(r"Domicilio:\s?(.*)"),
    re.compile(r"DOMICILIO POSTAL\s+(.*?)\s+Nº LIQUIDACIÓN DE FECHA DE EMISIÓN PROX."),
    re.compile(r"([A-Z\s\d]+)\nB° CENTRO"),
    re.compile(r"Domicilio suministro:\n(.+)"),  # Domicilio de suministro
]

# Regex patterns for extracting periods
period_regex = [
    re.compile(r"Periodo:\s?(.*)"),
    re.compile(r"(\d{2}/\d{2}/\d{2})\s?al\s?(\d{2}/\d{2}/\d{2})"),
    re.compile(r"Período de consumo (\d{4}/\d{2})"),
    re.compile(r"Período Facturado:\s(\w+ \d{4})"),
    re.compile(r"Período Facturado:\s(.+)"),  # Período facturado
    re.compile(r"BIM (\d{2}/\d{4})"),  # Período en formato BIM
]

# Regex patterns for extracting costs
cost_regex = [
    re.compile(r"Tipo Lectura: Real\n\$ \s?([0-9]+.[0-9]+,[0-9]+)"),
    re.compile(r"IMPORTE A PAGAR\n\$\s?([0-9]+.[0-9]+)"),
    re.compile(r"TOTAL PESOS: \$ ([0-9]+.[0-9]+)"),
    re.compile(r"TOTAL \$ ([0-9]+,[0-9]+)"),
    re.compile(r"TOTAL \$ ([0-9]+.[0-9]+,[0-9]+)"),
    re.compile(r"Costo:\s?(\$[0-9]+.[0-9]+)\s?Ref:"),
    re.compile(r"IMPORTE A PAGAR\s+\$?\s?(.*?)\s+DOMICILIO POSTAL"),
    re.compile(r"TOTAL A PAGAR \$\s(\d+.\d{2})"),
    re.compile(r"TOTAL \$\s(\d+.\d{2})"),
    re.compile(r"Total a pagar hasta el \d{2}/\d{2}/\d{4} \$ (\d+.\d{2})"),
    re.compile(r"\$([0-9]+.[0-9]+)"),
    re.compile(r"\$(\d+.\d{2})"),
    re.compile(r"TOTAL \$ (\d{1,3}(?:\.\d{3})*(?:,\d{2}))"),  # Total a pagar
    re.compile(r"Subtotal \$ (\d{1,3}(?:\.\d{3})*(?:,\d{2}))"),  # Subtotal
]

# Regex patterns for extracting consumption
consumption_regex = [
    re.compile(r"Cargo Variable kWh (\d+)"),  # Consumo en kWh
    re.compile(r"Consumo Medido\s+(\d+)\s*m³"),
]

# Dictionary to group all regex patterns
regex_patterns = {
    "date": date_regex,
    "address": address_regex,
    "period": period_regex,
    "cost": cost_regex,
    "consumption": consumption_regex,
}


def clean_text(text):
    """
    Limpia y normaliza el texto para facilitar la extracción de datos.
    """
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.upper()  # Normalizar a mayúsculas


def validate_date(date_str):
    """
    Valida que una fecha esté en el formato correcto (dd/mm/yyyy).
    """
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def extract_data(text, pattern_type):
    """
    Extracts data from text using the specified pattern type.

    :param text: The text to search.
    :param pattern_type: The type of pattern to use (e.g., 'date', 'address').
    :return: A list of matched data.
    """
    patterns = regex_patterns.get(pattern_type, [])
    matches = []
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            matches.append(match.group(1))
    return matches


async def convert_data_to_json(data):
    """
    Convierte los datos de una factura en formato JSON.
    """
    if not isinstance(data, str):
        data = str(data)

    # Limpiar y normalizar el texto
    data = clean_text(data)

    # Extraer datos
    date = extract_data(data, "date")
    address = extract_data(data, "address")
    consumption = extract_data(data, "consumption")
    period = extract_data(data, "period")
    cost = extract_data(data, "cost")

    # Validar y formatear los datos
    date = date[0] if date and validate_date(date[0]) else None
    address = address[0] if address else None
    consumption = consumption[0] if consumption else None
    period = period[0] if period else None
    cost = (
        "{:.2f}".format(float(cost[0].replace(".", "").replace(",", ".")))
        if cost and re.search(r"\.\d{3}", cost[0])
        else (("{:.2f}".format(float(cost[0].replace(",", "")))) if cost else None)
    )

    return {
        "date": date,
        "address": address,
        "consumption": consumption,
        "period": period,
        "cost": cost,
    }
