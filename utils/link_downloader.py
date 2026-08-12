import os
import re
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
import yt_dlp

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r'https?://[^\s]+')

VIDEO_DOMAINS = [
    'youtube.com', 'youtu.be',
    'instagram.com', 'instagr.am',
    'tiktok.com',
    'twitter.com', 'x.com',
    'facebook.com', 'fb.watch', 'fb.com',
    'vimeo.com', 'pinterest.com', 'pin.it',
    'reddit.com', 'douyin.com'
]


def extract_url(text: str) -> str | None:
    match = URL_REGEX.search(text)
    return match.group(0) if match else None


def is_video_url(url: str) -> bool:
    url_lower = url.lower()
    for domain in VIDEO_DOMAINS:
        if domain in url_lower:
            return True
    if any(kw in url_lower for kw in ['/reel/', '/reels/', '/shorts/', '/watch', '.mp4', '.mov', '.webm']):
        return True
    return False


def _extract_video_info(url: str) -> dict | None:
    ydl_opts = {
        'format': 'b[ext=mp4]/best[ext=mp4]/bestvideo[ext=mp4]+bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None

            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]

            direct_url = info.get('url')
            title = info.get('title') or "Video"
            thumbnail = info.get('thumbnail') or "https://png.pngtree.com/png-vector/20190215/ourmid/pngtree-play-video-icon-png-image_533038.jpg"

            return {
                "url": direct_url,
                "title": title,
                "thumbnail": thumbnail
            }
    except Exception as e:
        logger.error(f"yt-dlp extract_info error: {e}")
        return None


async def extract_video_info(url: str) -> dict | None:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_extract_video_info, url), timeout=8.0)
    except Exception:
        return None


def _ytdlp_download(url: str) -> str | None:
    output_tmpl = "/tmp/video_%(id)s.%(ext)s"
    ydl_opts = {
        'outtmpl': output_tmpl,
        'format': 'b[ext=mp4]/best[ext=mp4]/bestvideo[ext=mp4]+bestaudio/best',
        'max_filesize': 50 * 1024 * 1024,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 20,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None

            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                return filename

            file_id = info.get("id")
            if file_id:
                for f in os.listdir("/tmp"):
                    if file_id in f and not f.endswith(".part"):
                        return os.path.join("/tmp", f)
            return None
    except Exception as e:
        logger.error(f"yt-dlp download error for {url}: {e}")
        return None


async def download_video(url: str) -> str | None:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_ytdlp_download, url), timeout=45.0)
    except asyncio.TimeoutError:
        logger.error(f"yt-dlp download timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"yt-dlp async wrapper error: {e}")
        return None


async def scrape_webpage(url: str) -> str | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")

                    for s in soup(["script", "style", "nav", "footer", "header"]):
                        s.decompose()

                    text = soup.get_text(separator=" ", strip=True)
                    return text[:3000]
                return None
    except Exception as e:
        logger.error(f"Web scraping error for {url}: {e}")
        return None
