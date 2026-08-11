import re
import asyncio
import logging
import subprocess
import imageio_ffmpeg

logger = logging.getLogger(__name__)


def _get_video_duration(input_path: str) -> float:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-i", input_path]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+|\d+)", res.stderr)
        if match:
            hours = float(match.group(1))
            minutes = float(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
    except Exception as e:
        logger.error(f"Error probing video duration: {e}")
    return 0.0


def _extract_audio_or_gif(input_path: str, output_path: str, format_type: str) -> str:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    if format_type == "gif":
        duration = _get_video_duration(input_path)
        # Check 8 seconds limit (allow slight margin up to 8.5s)
        if duration > 8.5:
            raise ValueError("gif_too_long")
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-vf", "fps=10,scale=320:-1:flags=lanczos", "-c:v", "gif", output_path]
    elif format_type == "mp3":
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
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode('utf-8', errors='ignore')[:300]}")
        raise RuntimeError(f"FFmpeg conversion failed: {e.stderr.decode('utf-8', errors='ignore')[:100]}")


async def convert_video_to_gif(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio_or_gif, input_path, output_path, "gif")


async def convert_video_to_mp3(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio_or_gif, input_path, output_path, "mp3")


async def convert_video_to_ogg(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio_or_gif, input_path, output_path, "ogg")


async def convert_video_to_wav(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio_or_gif, input_path, output_path, "wav")


async def convert_video_to_m4a(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_extract_audio_or_gif, input_path, output_path, "m4a")


CONVERTERS = {
    ('mp4', 'gif'): convert_video_to_gif,
    ('mp4', 'mp3'): convert_video_to_mp3,
    ('mp4', 'ogg'): convert_video_to_ogg,
    ('mp4', 'wav'): convert_video_to_wav,
    ('mp4', 'm4a'): convert_video_to_m4a,
    ('avi', 'gif'): convert_video_to_gif,
    ('avi', 'mp3'): convert_video_to_mp3,
    ('avi', 'ogg'): convert_video_to_ogg,
    ('avi', 'wav'): convert_video_to_wav,
    ('avi', 'm4a'): convert_video_to_m4a,
    ('mov', 'gif'): convert_video_to_gif,
    ('mov', 'mp3'): convert_video_to_mp3,
    ('mov', 'ogg'): convert_video_to_ogg,
    ('mov', 'wav'): convert_video_to_wav,
    ('mov', 'm4a'): convert_video_to_m4a,
    ('mkv', 'gif'): convert_video_to_gif,
    ('mkv', 'mp3'): convert_video_to_mp3,
    ('mkv', 'ogg'): convert_video_to_ogg,
    ('mkv', 'wav'): convert_video_to_wav,
    ('mkv', 'm4a'): convert_video_to_m4a,
    ('webm', 'gif'): convert_video_to_gif,
    ('webm', 'mp3'): convert_video_to_mp3,
    ('webm', 'ogg'): convert_video_to_ogg,
    ('webm', 'wav'): convert_video_to_wav,
    ('webm', 'm4a'): convert_video_to_m4a,
}
