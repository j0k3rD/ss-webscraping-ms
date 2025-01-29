import os
from ..utils.extract_utils.req_backend import download_pdf, save_consumed_data
from ..utils.extract_utils.convert_data import convert_data_to_json
from ..utils.extract_utils.extract_data_from_pdf import extract_data_from_pdf


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
        user_service_id = data["user_service"]["id"]
        try:
            temp_dir_result = await download_pdf(user_service_id)
            if not isinstance(temp_dir_result, (str, tuple, list)):
                raise ValueError(f"Failed to download PDF: {temp_dir_result}")

            if isinstance(temp_dir_result, tuple):
                _, temp_dir = temp_dir_result
            else:
                temp_dir = temp_dir_result

            if isinstance(temp_dir, str):
                files = await self.get_files_in_directory(temp_dir)
                for pdf_file in files:
                    pdf_path = os.path.join(temp_dir, pdf_file)
                    extracted_data = await extract_data_from_pdf(pdf_path)
                    print(f"Extracted data: {extracted_data}")
                    json_data = await convert_data_to_json(extracted_data)
                    self.all_data.append(json_data)

            elif isinstance(temp_dir, list):
                for content in temp_dir:
                    if isinstance(content, dict) and "url" in content:
                        # Aquí podrías agregar lógica para manejar las URLs si es necesario
                        json_data = await convert_data_to_json(content)
                        self.all_data.append(json_data)
                    else:
                        print(f"Unexpected content type or missing 'url': {content}")

            if isinstance(self.all_data, list):
                self.all_data = {i: data for i, data in enumerate(self.all_data)}

            await save_consumed_data(user_service_id, self.all_data)

        except Exception as e:
            print(f"Error al procesar las facturas: {e}")

    async def get_files_in_directory(self, directory):
        """
        Obtiene una lista de archivos en un directorio dado.
        """
        return [
            f
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]
