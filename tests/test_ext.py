import pdfplumber


def extract_data_from_pdf(pdf_path):
    """
    Extrae texto de un archivo PDF, incluyendo todas las páginas.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"


extract_data_from_pdf("/home/j0k3r/home/Facultad/ss-webscraping-ms/fac_ay.pdf")
