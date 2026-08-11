import asyncio
import logging
import subprocess
import imageio_ffmpeg

logger = logging.getLogger(__name__)


def _extract_audio(input_path: str, output_path: str, format_type: str) -> str:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    if format_type == "mp3":
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", output_path]
    elif format_type == "ogg":
        # Telegram Voice Note format (Opus in OGG container)
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-vn", "-c:a", "libopus", "-b:a", "64k", output_path]
    elif format_type == "wav":
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-vn", "-acodec", "pcm_s16le", output_path]
    elif format_type == "m4a":
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-vn", "-c:a", "aac", "-b:a", "192k", output_path]
    else:
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-vn", output_path]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode('utf-8', errors='ignore')[:300]}")
        raise RuntimeError(f"FFmpeg conversion failed: {e.stderr.decode('utf-8', errors='ignore')[:100]}")


async def convert_video_to_mp3(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio, input_path, output_path, "mp3")


async def convert_video_to_ogg(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio, input_path, output_path, "ogg")


async def convert_video_to_wav(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio, input_path, output_path, "wav")


async def convert_video_to_m4a(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio, input_path, output_path, "m4a")


CONVERTERS = {
    ('mp4', 'mp3'): convert_video_to_mp3,
    ('mp4', 'ogg'): convert_video_to_ogg,
    ('mp4', 'wav'): convert_video_to_wav,
    ('mp4', 'm4a'): convert_video_to_m4a,
    ('avi', 'mp3'): convert_video_to_mp3,
    ('avi', 'ogg'): convert_video_to_ogg,
    ('avi', 'wav'): convert_video_to_wav,
    ('avi', 'm4a'): convert_video_to_m4a,
    ('mov', 'mp3'): convert_video_to_mp3,
    ('mov', 'ogg'): convert_video_to_ogg,
    ('mov', 'wav'): convert_video_to_wav,
    ('mov', 'm4a'): convert_video_to_m4a,
    ('mkv', 'mp3'): convert_video_to_mp3,
    ('mkv', 'ogg'): convert_video_to_ogg,
    ('mkv', 'wav'): convert_video_to_wav,
    ('mkv', 'm4a'): convert_video_to_m4a,
    ('webm', 'mp3'): convert_video_to_mp3,
    ('webm', 'ogg'): convert_video_to_ogg,
    ('webm', 'wav'): convert_video_to_wav,
    ('webm', 'm4a'): convert_video_to_m4a,
}
