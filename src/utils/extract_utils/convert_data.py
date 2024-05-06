import re

date_regex = re.compile(r"Fecha:\s?(\d{2}/\d{2}/\d{2})"), re.compile(r"Fecha?:\s?(\d{2}/\d{2}/\d{4})")
address_regex = re.compile(r"Domicilio:\s?(.*)")
period_regex = re.compile(r"Periodo:\s?(.*)"), re.compile(r"\s?(\d{2}/\d{2}/\d{4})\s?-\s?(\d{2}/\d{2}/\d{4})")
cost_regex = re.compile(r"\$([0-9]+.[0-9]+)"), re.compile(r"Costo:\s?(\$[0-9]+.[0-9]+)\s?Ref:")


async def convert_data_to_json(data):
    """
    Convierte los datos de una factura en formato JSON.
    """
    # Asegúrate de que data es una cadena de texto
    if not isinstance(data, str):
        data = str(data)

    date = next((re.search(regex, data) for regex in date_regex if re.search(regex, data) is not None), None)
    address = re.search(address_regex, data)
    period = next((re.search(regex, data) for regex in period_regex if re.search(regex, data) is not None), None)
    cost = next((re.search(regex, data) for regex in cost_regex if re.search(regex, data) is not None), None)

    return {
        "date": date.group(1) if date else None,
        "address": address.group(1) if address else None,
        "period": period.group(1) if period else None,
        "cost": cost.group(1) if cost else None
    }