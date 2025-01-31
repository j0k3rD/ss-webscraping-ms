import pdfplumber


async def extract_data_from_pdf(pdf_path):
    print("EXTRACT DATA FROM PDF")
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        print("text pdf", text)

    return text
