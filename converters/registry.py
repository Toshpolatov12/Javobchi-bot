import logging
from typing import Callable, Dict, Tuple, List

from . import images, documents, spreadsheets, data_formats, archives, ebooks, video

logger = logging.getLogger(__name__)

CONVERTERS: Dict[Tuple[str, str], Callable] = {}

# Combine all converters
for module in [images, documents, spreadsheets, data_formats, archives, ebooks, video]:
    if hasattr(module, 'CONVERTERS'):
        CONVERTERS.update(module.CONVERTERS)


def get_available_formats(file_extension: str) -> List[str]:
    ext = file_extension.lower().lstrip('.')
    return sorted(list(set(out_ext for in_ext, out_ext in CONVERTERS.keys() if in_ext == ext)))


def get_converter(input_ext: str, output_ext: str) -> Callable:
    in_e = input_ext.lower().lstrip('.')
    out_e = output_ext.lower().lstrip('.')
    return CONVERTERS.get((in_e, out_e))


def get_file_category(ext: str) -> str:
    ext = ext.lower().lstrip('.')
    if ext in ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'ico', 'heic']:
        return 'image'
    elif ext in ['docx', 'pdf', 'txt', 'md', 'html']:
        return 'document'
    elif ext in ['xlsx', 'xls', 'csv']:
        return 'spreadsheet'
    elif ext in ['zip', '7z', 'tar', 'tar.gz', 'gz']:
        return 'archive'
    elif ext in ['json', 'xml', 'yaml', 'yml']:
        return 'data'
    elif ext in ['epub']:
        return 'ebook'
    elif ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
        return 'video'
    return 'unknown'
