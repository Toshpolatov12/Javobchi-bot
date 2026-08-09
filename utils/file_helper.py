import os
from bot.config import TEMP_DIR

async def download_file(bot, file_id: str) -> tuple[str, str]:
    file = await bot.get_file(file_id)
    orig_name = file.file_path.split("/")[-1]
    path = os.path.join(TEMP_DIR, orig_name)
    await bot.download_file(file.file_path, path)
    return path, orig_name

def get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()

def cleanup(*paths):
    for p in paths:
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass

def generate_output_path(input_name: str, target_ext: str) -> str:
    base = input_name.rsplit(".", 1)[0] if "." in input_name else input_name
    return os.path.join(TEMP_DIR, f"{base}.{target_ext}")

def get_mime_type(ext: str) -> str:
    mimes = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "png": "image/png",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
    return mimes.get(ext, "application/octet-stream")
