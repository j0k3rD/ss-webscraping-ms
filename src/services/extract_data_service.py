import os
from ..utils.extract_utils.req_backend import (
    download_pdf,
    get_data_by_user_service_id,
    save_consumed_data,
)
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
            # Step 1: Check if bills_url contains content
            scrapped_data = await get_data_by_user_service_id(user_service_id)
            if not scrapped_data or not isinstance(scrapped_data, dict):
                raise ValueError(f"Invalid scrapped_data: {scrapped_data}")

            bills_url = scrapped_data.get("bills_url", [])
            if not isinstance(bills_url, list):
                raise ValueError(
                    f"Unexpected data type for bills_url: {type(bills_url)}"
                )

            # Step 2: Process bills_url
            for bill in bills_url:
                if not isinstance(bill, dict):
                    print(f"Unexpected data type for bill: {type(bill)}")
                    continue

                # If content is available, skip download and proceed to extraction
                if "content" in bill:
                    print(
                        "Content found, skipping download and proceeding to extraction."
                    )
                    json_data = await convert_data_to_json(bill)
                    print("PASAAA")

                    self.all_data.append(json_data)
                elif "url" in bill:
                    # If URL is available, download the PDF and extract data
                    print("URL found, downloading PDF and extracting data.")
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
                            json_data = await convert_data_to_json(extracted_data)
                            self.all_data.append(json_data)
                else:
                    print(f"Unexpected bill format: {bill}")

            print("PASA#")
            # Convert all_data to a dictionary if it's a list
            if isinstance(self.all_data, list):
                self.all_data = {i: data for i, data in enumerate(self.all_data)}
            print("PASAE")
            # Step 3: Save the processed data
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
