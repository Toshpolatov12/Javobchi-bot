import asyncio
import logging
import pandas as pd
from fpdf import FPDF
import urllib.request
import os

logger = logging.getLogger(__name__)

def get_dejavu_font():
    font_path = "/tmp/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
            urllib.request.urlretrieve(url, font_path)
        except Exception as e:
            logger.error(f"Failed to download DejaVu font: {e}")
    return font_path

def _xlsx_to_csv(input_path: str, output_path: str) -> str:
    try:
        df = pd.read_excel(input_path, engine='openpyxl')
        df.to_csv(output_path, index=False)
        return output_path
    except Exception as e:
        logger.error(f"Error converting xlsx to csv: {e}")
        raise

async def convert_xlsx_to_csv(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_xlsx_to_csv, input_path, output_path)

def _csv_to_xlsx(input_path: str, output_path: str) -> str:
    try:
        df = pd.read_csv(input_path)
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path
    except Exception as e:
        logger.error(f"Error converting csv to xlsx: {e}")
        raise

async def convert_csv_to_xlsx(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_csv_to_xlsx, input_path, output_path)

def _xlsx_to_json(input_path: str, output_path: str) -> str:
    try:
        df = pd.read_excel(input_path, engine='openpyxl')
        df.to_json(output_path, orient='records', indent=4)
        return output_path
    except Exception as e:
        logger.error(f"Error converting xlsx to json: {e}")
        raise

async def convert_xlsx_to_json(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_xlsx_to_json, input_path, output_path)

def _json_to_csv(input_path: str, output_path: str) -> str:
    try:
        df = pd.read_json(input_path)
        df.to_csv(output_path, index=False)
        return output_path
    except Exception as e:
        logger.error(f"Error converting json to csv: {e}")
        raise

async def convert_json_to_csv(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_json_to_csv, input_path, output_path)

def _csv_to_json(input_path: str, output_path: str) -> str:
    try:
        df = pd.read_csv(input_path)
        df.to_json(output_path, orient='records', indent=4)
        return output_path
    except Exception as e:
        logger.error(f"Error converting csv to json: {e}")
        raise

async def convert_csv_to_json(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_csv_to_json, input_path, output_path)

def _xls_to_xlsx(input_path: str, output_path: str) -> str:
    try:
        df = pd.read_excel(input_path, engine='xlrd')
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path
    except Exception as e:
        logger.error(f"Error converting xls to xlsx: {e}")
        raise

async def convert_xls_to_xlsx(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_xls_to_xlsx, input_path, output_path)

def _xlsx_to_pdf(input_path: str, output_path: str) -> str:
    try:
        df = pd.read_excel(input_path, engine='openpyxl')
        
        pdf = FPDF()
        pdf.add_page()
        font_path = get_dejavu_font()
        if os.path.exists(font_path):
            pdf.add_font("DejaVu", "", font_path, uni=True)
            pdf.set_font("DejaVu", size=10)
        else:
            pdf.set_font("Arial", size=10)
            
        text = df.to_string()
        pdf.multi_cell(0, 5, text)
        pdf.output(output_path)
        return output_path
    except Exception as e:
        logger.error(f"Error converting xlsx to pdf: {e}")
        raise

async def convert_xlsx_to_pdf(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_xlsx_to_pdf, input_path, output_path)

CONVERTERS = {
    ('xlsx', 'csv'): convert_xlsx_to_csv,
    ('csv', 'xlsx'): convert_csv_to_xlsx,
    ('xlsx', 'json'): convert_xlsx_to_json,
    ('json', 'csv'): convert_json_to_csv,
    ('csv', 'json'): convert_csv_to_json,
    ('xls', 'xlsx'): convert_xls_to_xlsx,
    ('xlsx', 'pdf'): convert_xlsx_to_pdf,
}
