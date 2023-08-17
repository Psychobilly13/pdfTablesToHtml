from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import camelot
import os
import uuid
import html
import tempfile
from img2table.document import PDF
from img2table.ocr import TesseractOCR
from dotenv import load_dotenv

load_dotenv()

# logic
async def recognize_pdf_with_text(file: str):
    # read data from saving file
    tables = camelot.read_pdf(file, pages='all', line_scale=40)

    # create html string from pdf data
    html = ""
    for table in tables:
        html += table.df.to_html()
    
    return html

async def recognize_pdf_with_image(file: str):
    tesseract_ocr = TesseractOCR(n_threads=8, lang="rus")
    # confidence
    min_recognizing_confidence = int(os.getenv("MIN_RECOGNIZING_CONFIDENCE"))

    pdf = PDF(src=file)
    extracted_tables = pdf.extract_tables(ocr=tesseract_ocr, implicit_rows=True, borderless_tables=True, min_confidence=min_recognizing_confidence)

    # create html string from images of pdf
    html = ''
    for page, tables in extracted_tables.items():
        for idx, table in enumerate(tables):
            # create page and merge this with other pages
            html += table.html_repr(title=f"Page {page + 1} - Extracted table # {idx + 1}")
    
    return html

# API
app = FastAPI()

@app.post("/")
async def recognize_pdf(file: UploadFile = File(...)):
    try:
        10 / 0;
        # create file path
        local_db = tempfile.gettempdir()
        print(local_db)
        file_path = f"{local_db}/{file.filename}"

        # save file
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # logic for recognizing
        result = ""
        # if this recognize will be ok we don't need use tesseract
        result = await recognize_pdf_with_text(file_path)

        if result == "":
            # tesseract logic
            result = await recognize_pdf_with_image(file_path)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="something wrong")
    


