import re

date_regex = [
    re.compile(r"Fecha:\s?(\d{2}/\d{2}/\d{2})"),
    re.compile(r"Vto.:\s?(\d{2}/\d{2}/\d{4})"),
    re.compile(r"al:\s?(\d{2}/\d{2}/\d{4})"),
    re.compile(r"Fecha de emisión:\s(\d{2}/\d{2}/\d{4})")
]
address_regex = [re.compile(r"Domicilio:\s?(.*)"), re.compile(r"DOMICILIO POSTAL\s+(.*?)\s+Nº LIQUIDACIÓN DE FECHA DE EMISIÓN PROX."), re.compile(r"([A-Z\s\d]+)\nB° CENTRO"), re.compile(r"Domicilio suministro:\n(.+)")]
period_regex = [re.compile(r"Periodo:\s?(.*)"), re.compile(r"(\d{2}/\d{2}/\d{2})\s?al\s?(\d{2}/\d{2}/\d{2})"), re.compile(r"Período de consumo (\d{4}/\d{2})"), re.compile(r"Período Facturado:\s(\w+ \d{4})")]
cost_regex = [re.compile(r"\$([0-9]+.[0-9]+)"), re.compile(r"Costo:\s?(\$[0-9]+.[0-9]+)\s?Ref:"), re.compile(r"IMPORTE A PAGAR\s+\$?\s?(.*?)\s+DOMICILIO POSTAL"), re.compile(r"TOTAL A PAGAR \$\s(\d+.\d{2})"), re.compile(r"TOTAL \$\s(\d+.\d{2})"), re.compile(r"\$(\d+.\d{2})"),]


async def convert_data_to_json(data):
    """
    Convierte los datos de una factura en formato JSON.
    """
    # Asegúrate de que data es una cadena de texto
    if not isinstance(data, str):
        data = str(data)

    date = next((re.search(regex, data) for regex in date_regex if re.search(regex, data) is not None), None)
    address = next((re.search(regex, data) for regex in address_regex if re.search(regex, data) is not None), None)
    period = next((re.search(regex, data) for regex in period_regex if re.search(regex, data) is not None), None)
    cost = next((re.search(regex, data) for regex in cost_regex if re.search(regex, data) is not None), None)

    return {
        "date": date.group(1) if date else None,
        "address": address.group(1) if address else None,
        "period": period.group(1) if period else None,
        "cost": cost.group(1) if cost else None
    }