from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import camelot
import os
import uuid
import html
import tempfile
import ghostscript
from img2table.document import PDF
from img2table.ocr import TesseractOCR
from dotenv import load_dotenv
import PyPDF2

load_dotenv()

# logic
async def recognize_pdf_extractable_text(file: str, page=str):
    # read data from saving file
    try:
        # check pages
        tables = camelot.read_pdf(file, pages=page, line_scale=40)
        # create html string from pdf data
        html = ""
        for table in tables:
            print(table.parsing_report)
            if table.parsing_report["accuracy"] < 60:
                return ""
            html += table.df.to_html()
    
        return html
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"recognize_pdf_extractable_text_failed:\n{e}")

async def recognize_pdf_recognizable(file: str, page=str):
    try:
        tesseract_ocr = TesseractOCR(n_threads=8, lang="rus")
        # confidence
        min_recognizing_confidence = int(os.getenv("MIN_RECOGNIZING_CONFIDENCE"))
        page_option = None
        if page == "1-4":
            page_option = [0,1,2,3]
        
        pdf = PDF(src=file, pages=page_option)
        
        
        extracted_tables = pdf.extract_tables(ocr=tesseract_ocr, implicit_rows=True, borderless_tables=True, min_confidence=min_recognizing_confidence)

        # create html string from images of pdf
        html = ""
        for page, tables in extracted_tables.items():
            for idx, table in enumerate(tables):
                # create page and merge this with other pages
                html += table.html_repr(title=f"Page {page + 1} - Extracted table # {idx + 1}")
    
        return html
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"recognize_pdf_recognizable_failed:\n{e}")


# API
app = FastAPI()

@app.post("/")
async def recognize_pdf(file: UploadFile = File(...)):
    try:
        print("start recognizing")
        # create file path
        local_db = tempfile.gettempdir()
        file_path = f"{local_db}/{file.filename}"

        # save file
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        pages_length = 0
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages_length = len(pdf_reader.pages)
        pages = "all"
        if pages_length > 5:
            pages = "1-4"

        # logic for recognizing
        status = True
        result = ""
        pdf_type = "extractableText"
        # if this recognize will be ok we don"t need use tesseract
        result = await recognize_pdf_extractable_text(file_path, pages)

        if result == "":
            # tesseract logic
            pdf_type = "recognizable"
            result = await recognize_pdf_recognizable(file_path, pages)
        
        if result == "":
            pdf_type = "unknown"
            status = False

        return {"type": pdf_type, "status": status, "result": result}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@app.post("/{pdf_type}")
async def recognize_pdf(pdf_type: str, file: UploadFile = File(...)):
    try:
        # create file path
        local_db = tempfile.gettempdir()
        file_path = f"{local_db}/{file.filename}"

        # save file
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        pages_length = 0
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages_length = len(pdf_reader.pages)
        pages = "all"
        if pages_length > 5:
            pages = "1-4"

        if pdf_type == "extractableText":
            # logic for recognizing
            status = True
            result = await recognize_pdf_extractable_text(file_path, pages)

            if result == "":
                status = False
        
        if pdf_type == "recognizable":
            # logic for recognizing
            status = True
            result = await recognize_pdf_recognizable(file_path, pages)

            if result == "":
                pdf_type = "unknown"
                status = False


        return {"type": pdf_type,"status": status, "result": result}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)