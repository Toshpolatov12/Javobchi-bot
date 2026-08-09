import asyncio
import logging
from PIL import Image
import pillow_heif

logger = logging.getLogger(__name__)

def _convert_image(input_path: str, output_path: str, format: str, **kwargs) -> str:
    try:
        with Image.open(input_path) as img:
            if format in ['JPEG', 'BMP'] and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(output_path, format=format, **kwargs)
        return output_path
    except Exception as e:
        logger.error(f"Error converting image {input_path} to {format}: {e}")
        raise

async def convert_png_to_jpg(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'JPEG')

async def convert_jpg_to_png(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'PNG')

async def convert_png_to_webp(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'WEBP')

async def convert_webp_to_png(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'PNG')

async def convert_png_to_bmp(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'BMP')

async def convert_bmp_to_png(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'PNG')

async def convert_png_to_tiff(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'TIFF')

async def convert_tiff_to_png(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'PNG')

def _convert_to_ico(input_path: str, output_path: str) -> str:
    try:
        with Image.open(input_path) as img:
            img = img.resize((256, 256))
            img.save(output_path, format='ICO')
        return output_path
    except Exception as e:
        logger.error(f"Error converting image {input_path} to ICO: {e}")
        raise

async def convert_png_to_ico(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_to_ico, input_path, output_path)

async def convert_ico_to_png(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'PNG')

async def convert_jpg_to_webp(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'WEBP')

async def convert_webp_to_jpg(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'JPEG')

async def convert_jpg_to_bmp(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'BMP')

async def convert_bmp_to_jpg(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'JPEG')

async def convert_jpg_to_tiff(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'TIFF')

async def convert_tiff_to_jpg(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_image, input_path, output_path, 'JPEG')

def _convert_heic_to_jpg(input_path: str, output_path: str) -> str:
    try:
        heif_file = pillow_heif.read_heif(input_path)
        img = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
        )
        img.save(output_path, format="JPEG")
        return output_path
    except Exception as e:
        logger.error(f"Error converting HEIC to JPG {input_path}: {e}")
        raise

async def convert_heic_to_jpg(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_convert_heic_to_jpg, input_path, output_path)

CONVERTERS = {
    ('png', 'jpg'): convert_png_to_jpg,
    ('png', 'jpeg'): convert_png_to_jpg,
    ('jpg', 'png'): convert_jpg_to_png,
    ('jpeg', 'png'): convert_jpg_to_png,
    ('png', 'webp'): convert_png_to_webp,
    ('webp', 'png'): convert_webp_to_png,
    ('png', 'bmp'): convert_png_to_bmp,
    ('bmp', 'png'): convert_bmp_to_png,
    ('png', 'tiff'): convert_png_to_tiff,
    ('tiff', 'png'): convert_tiff_to_png,
    ('png', 'ico'): convert_png_to_ico,
    ('ico', 'png'): convert_ico_to_png,
    ('jpg', 'webp'): convert_jpg_to_webp,
    ('jpeg', 'webp'): convert_jpg_to_webp,
    ('webp', 'jpg'): convert_webp_to_jpg,
    ('webp', 'jpeg'): convert_webp_to_jpg,
    ('jpg', 'bmp'): convert_jpg_to_bmp,
    ('jpeg', 'bmp'): convert_jpg_to_bmp,
    ('bmp', 'jpg'): convert_bmp_to_jpg,
    ('bmp', 'jpeg'): convert_bmp_to_jpg,
    ('jpg', 'tiff'): convert_jpg_to_tiff,
    ('jpeg', 'tiff'): convert_jpg_to_tiff,
    ('tiff', 'jpg'): convert_tiff_to_jpg,
    ('tiff', 'jpeg'): convert_tiff_to_jpg,
    ('heic', 'jpg'): convert_heic_to_jpg,
    ('heic', 'jpeg'): convert_heic_to_jpg,
}
