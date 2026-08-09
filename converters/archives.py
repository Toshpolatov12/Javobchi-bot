import asyncio
import logging
import zipfile
import py7zr
import tarfile
import os
import shutil

logger = logging.getLogger(__name__)

def _extract_zip(input_path: str, output_path: str) -> str:
    # Just extracts and repacks flat or returns a generic zip
    # We will just return the extracted files in a new zip if requested, or same
    # Easiest way to "convert" ZIP to ZIP is to copy it or rebuild it.
    try:
        shutil.copy(input_path, output_path)
        return output_path
    except Exception as e:
        logger.error(f"Error processing ZIP: {e}")
        raise

async def extract_zip_to_zip(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_zip, input_path, output_path)

def _7z_to_zip(input_path: str, output_path: str) -> str:
    tmp_dir = input_path + "_tmp"
    try:
        os.makedirs(tmp_dir, exist_ok=True)
        with py7zr.SevenZipFile(input_path, mode='r') as z:
            z.extractall(path=tmp_dir)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmp_dir)
                    zipf.write(file_path, arcname)
        return output_path
    except Exception as e:
        logger.error(f"Error converting 7z to zip: {e}")
        raise
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

async def convert_7z_to_zip(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_7z_to_zip, input_path, output_path)

def _tar_to_zip(input_path: str, output_path: str) -> str:
    tmp_dir = input_path + "_tmp"
    try:
        os.makedirs(tmp_dir, exist_ok=True)
        with tarfile.open(input_path, 'r:*') as tar:
            tar.extractall(path=tmp_dir)
            
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmp_dir)
                    zipf.write(file_path, arcname)
        return output_path
    except Exception as e:
        logger.error(f"Error converting tar to zip: {e}")
        raise
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

async def convert_tar_to_zip(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_tar_to_zip, input_path, output_path)

def _zip_to_tar(input_path: str, output_path: str) -> str:
    tmp_dir = input_path + "_tmp"
    try:
        os.makedirs(tmp_dir, exist_ok=True)
        with zipfile.ZipFile(input_path, 'r') as zipf:
            zipf.extractall(path=tmp_dir)
            
        with tarfile.open(output_path, 'w') as tar:
            tar.add(tmp_dir, arcname=os.path.basename(tmp_dir))
        return output_path
    except Exception as e:
        logger.error(f"Error converting zip to tar: {e}")
        raise
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

async def convert_zip_to_tar(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_zip_to_tar, input_path, output_path)

def _zip_to_7z(input_path: str, output_path: str) -> str:
    tmp_dir = input_path + "_tmp"
    try:
        os.makedirs(tmp_dir, exist_ok=True)
        with zipfile.ZipFile(input_path, 'r') as zipf:
            zipf.extractall(path=tmp_dir)
            
        with py7zr.SevenZipFile(output_path, 'w') as z:
            z.writeall(tmp_dir, arcname=os.path.basename(tmp_dir))
        return output_path
    except Exception as e:
        logger.error(f"Error converting zip to 7z: {e}")
        raise
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

async def convert_zip_to_7z(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_zip_to_7z, input_path, output_path)

CONVERTERS = {
    ('zip', 'zip'): extract_zip_to_zip,
    ('7z', 'zip'): convert_7z_to_zip,
    ('tar', 'zip'): convert_tar_to_zip,
    ('tar.gz', 'zip'): convert_tar_to_zip,
    ('gz', 'zip'): convert_tar_to_zip,
    ('zip', 'tar'): convert_zip_to_tar,
    ('zip', '7z'): convert_zip_to_7z,
}
