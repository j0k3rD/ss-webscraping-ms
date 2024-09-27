import re

date_regex = [
    re.compile(r"Vto.:\s(\d{2}/\d{2}/\d{4})"),
    re.compile(r"PERIODO\s(\d{2}/\d{2}/\d{2})"),
    re.compile(r"Fecha:\s?(\d{2}/\d{2}/\d{2})"),
    re.compile(r"Vto.:\s?(\d{2}/\d{2}/\d{4})"),
    re.compile(r"al:\s?(\d{2}/\d{2}/\d{4})"),
    re.compile(r"Fecha de emisión:\s(\d{2}/\d{2}/\d{4})"),
]
address_regex = [
    re.compile(r"DOMICILIO POSTAL\n(.+?)\n"),
    re.compile(r"Domicilio:\s?(.*)"),
    re.compile(r"DOMICILIO POSTAL\s+(.*?)\s+Nº LIQUIDACIÓN DE FECHA DE EMISIÓN PROX."),
    re.compile(r"([A-Z\s\d]+)\nB° CENTRO"),
    re.compile(r"Domicilio suministro:\n(.+)"),
]
period_regex = [
    re.compile(r"Periodo:\s?(.*)"),
    re.compile(r"(\d{2}/\d{2}/\d{2})\s?al\s?(\d{2}/\d{2}/\d{2})"),
    re.compile(r"Período de consumo (\d{4}/\d{2})"),
    re.compile(r"Período Facturado:\s(\w+ \d{4})"),
]
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
]
consumption_regex = [
    re.compile(r"Cargo Variable kWh (\d+)"),
    re.compile(r"Consumo Medido (\d+) m³"),
    re.compile(r"Cargo Variable kWh (\d+)"),
]


async def convert_data_to_json(data):
    """
    Convierte los datos de una factura en formato JSON.
    """
    # Asegúrate de que data es una cadena de texto
    if not isinstance(data, str):
        data = str(data)

    date = next(
        (
            re.search(regex, data)
            for regex in date_regex
            if re.search(regex, data) is not None
        ),
        None,
    )
    address = next(
        (
            re.search(regex, data)
            for regex in address_regex
            if re.search(regex, data) is not None
        ),
        None,
    )
    consumption = next(
        (
            re.search(regex, data)
            for regex in consumption_regex
            if re.search(regex, data) is not None
        ),
        None,
    )
    period = next(
        (
            re.search(regex, data)
            for regex in period_regex
            if re.search(regex, data) is not None
        ),
        None,
    )
    cost = next(
        (
            re.search(regex, data)
            for regex in cost_regex
            if re.search(regex, data) is not None
        ),
        None,
    )

    return {
        "date": date.group(1) if date else None,
        "address": address.group(1) if address else None,
        "consumption": consumption.group(1) if consumption else None,
        "period": period.group(1) if period else None,
        "cost": (
            "{:.2f}".format(float(cost.group(1).replace(".", "").replace(",", ".")))
            if cost and re.search(r"\.\d{3}", cost.group(1))
            else (
                ("{:.2f}".format(float(cost.group(1).replace(",", ""))))
                if cost
                else None
            )
        ),
    }

    if all(value is None for value in result.values()):
        return None

    return result
