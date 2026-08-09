import asyncio
import logging
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
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

def _extract_epub_text(input_path: str) -> str:
    book = epub.read_epub(input_path)
    text_content = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            text_content.append(soup.get_text())
    return "\n".join(text_content)

def _epub_to_txt(input_path: str, output_path: str) -> str:
    try:
        text = _extract_epub_text(input_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return output_path
    except Exception as e:
        logger.error(f"Error converting epub to txt: {e}")
        raise

async def convert_epub_to_txt(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_epub_to_txt, input_path, output_path)

def _epub_to_pdf(input_path: str, output_path: str) -> str:
    try:
        text = _extract_epub_text(input_path)
        pdf = FPDF()
        pdf.add_page()
        font_path = get_dejavu_font()
        if os.path.exists(font_path):
            pdf.add_font("DejaVu", "", font_path, uni=True)
            pdf.set_font("DejaVu", size=12)
        else:
            pdf.set_font("Arial", size=12)
        
        pdf.multi_cell(0, 10, text)
        pdf.output(output_path)
        return output_path
    except Exception as e:
        logger.error(f"Error converting epub to pdf: {e}")
        raise

async def convert_epub_to_pdf(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_epub_to_pdf, input_path, output_path)

CONVERTERS = {
    ('epub', 'txt'): convert_epub_to_txt,
    ('epub', 'pdf'): convert_epub_to_pdf,
}
