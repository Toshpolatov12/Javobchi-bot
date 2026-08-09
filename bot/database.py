import logging
import httpx
from bot.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)


def _headers(prefer: str = "") -> dict:
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _request(method: str, endpoint: str, **kwargs) -> dict | list | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase not configured")
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
            resp = await getattr(client, method)(url, **kwargs)
            if resp.status_code in (200, 201):
                return resp.json()
            logger.error(f"Supabase {method.upper()} {endpoint}: {resp.status_code} {resp.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"Supabase error: {e}")
        return None


async def init_db() -> bool:
    result = await _request("get", "users?select=id&limit=1", headers=_headers())
    return result is not None


async def save_user(user_id: int, username: str, full_name: str, language: str):
    data = {
        "id": user_id,
        "username": username or "",
        "full_name": full_name or "",
        "language": language
    }
    await _request(
        "post", "users",
        headers=_headers("resolution=merge-duplicates"),
        json=data
    )


async def log_file_activity(
    user_id: int, file_name: str, file_type: str,
    file_size: int, action: str, target_format: str, status: str
):
    data = {
        "user_id": user_id,
        "file_name": file_name or "unknown",
        "file_type": file_type or "unknown",
        "file_size": file_size or 0,
        "action": action,
        "target_format": target_format,
        "status": status
    }
    await _request("post", "activities", headers=_headers(), json=data)


async def get_user_stats(user_id: int) -> int:
    result = await _request(
        "get",
        f"activities?user_id=eq.{user_id}&select=id",
        headers=_headers()
    )
    return len(result) if result else 0


async def get_all_users_count() -> int:
    result = await _request("get", "users?select=id", headers=_headers())
    return len(result) if result else 0


async def get_recent_activities(limit: int = 50) -> list:
    result = await _request(
        "get",
        f"activities?select=*&order=created_at.desc&limit={limit}",
        headers=_headers()
    )
    return result if result else []


async def get_user_lang(user_id: int) -> str:
    result = await _request(
        "get",
        f"users?id=eq.{user_id}&select=language",
        headers=_headers()
    )
    if result and len(result) > 0:
        return result[0].get("language", "uz")
    return "uz"
