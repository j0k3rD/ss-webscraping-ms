import os
from ..utils.extract_utils.req_backend import download_pdf, save_consumed_data
from ..utils.extract_utils.convert_data import convert_data_to_json
from ..utils.extract_utils.extract_data_from_pdf import extract_data_from_pdf
from datetime import datetime


class ExtractDataService:
    """
    Servicio para procesar facturas.
    """

    def __init__(self):
        self.all_data = []

    async def plumb_bills(self, data):
        """
        Descarga, procesa y guarda facturas para un número de cliente dado.
        """
        provider_client_id = data["provider_client"]["id"]
        try:
            temp_dir_result = await download_pdf(provider_client_id)
            if isinstance(temp_dir_result, tuple):
                _, temp_dir = temp_dir_result
            else:
                temp_dir = temp_dir_result

            if isinstance(temp_dir, str):
                files = await self.get_files_in_directory(temp_dir)
                for pdf_file in files:
                    pdf_path = os.path.join(temp_dir, pdf_file)
                    json_data = await convert_data_to_json(data)
                    data = await extract_data_from_pdf(pdf_path)
                    # print(f"Data: {data}")
                    self.all_data.append(json_data)
                all_data_sorted = sorted(self.all_data, key=self.sort_key)
                await save_consumed_data(provider_client_id, all_data_sorted)

            if isinstance(temp_dir, list):
                for content in temp_dir:
                    json_data = await convert_data_to_json(content)
                    # print(f"Content: {content}")
                    self.all_data.append(json_data)
                all_data_sorted = sorted(self.all_data, key=self.sort_key)
                await save_consumed_data(provider_client_id, all_data_sorted)

        except Exception as e:
            print(f"Error al procesar las facturas: {e}")

    async def get_files_in_directory(self, directory):
        """
        Obtiene la lista de archivos en un directorio dado.
        """
        return os.listdir(directory)

    def sort_key(self, item):
        date = item["date"]
        if isinstance(date, list):
            date = tuple(date)
        if date is not None:
            date = datetime.strptime(date, "%d/%m/%y")
        return (date is None, date)
