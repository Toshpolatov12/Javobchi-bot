import logging
import httpx
from bot.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

MAX_ACTIVITY_LOGS = 2000  # FIFO Pruning limit to keep Supabase storage free & safe


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
            if resp.status_code in (200, 201, 204):
                if resp.status_code == 204 or not resp.text.strip():
                    return []
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


async def prune_old_activities(max_rows: int = MAX_ACTIVITY_LOGS):
    """FIFO Auto-Pruning: Keeps activities table size within free limit without touching users table."""
    try:
        result = await _request("get", "activities?select=id&order=id.asc", headers=_headers())
        if result and isinstance(result, list) and len(result) > max_rows:
            overflow = len(result) - max_rows
            ids_to_delete = [str(r["id"]) for r in result[:overflow] if "id" in r]
            if ids_to_delete:
                ids_str = ",".join(ids_to_delete)
                await _request("delete", f"activities?id=in.({ids_str})", headers=_headers())
                logger.info(f"Supabase FIFO Pruner deleted {len(ids_to_delete)} old activity logs.")
    except Exception as e:
        logger.error(f"Error during Supabase activity log pruning: {e}")


async def log_activity(user_id: int, action_type: str, content: str, status: str = "success", bot_username: str = ""):
    """Enhanced logging for user actions, including bot_username identifier for Multi-Bot analytics."""
    action_label = f"{action_type} [{bot_username}]" if bot_username else action_type
    data = {
        "user_id": user_id,
        "file_name": content[:100] if content else "unknown",
        "file_type": action_type,
        "file_size": 0,
        "action": action_label,
        "target_format": status,
        "status": status
    }
    await _request("post", "activities", headers=_headers(), json=data)
    await prune_old_activities()


async def log_file_activity(
    user_id: int, file_name: str, file_type: str,
    file_size: int, action: str, target_format: str, status: str, bot_username: str = ""
):
    action_label = f"{action} [{bot_username}]" if bot_username else action
    data = {
        "user_id": user_id,
        "file_name": file_name or "unknown",
        "file_type": file_type or "unknown",
        "file_size": file_size or 0,
        "action": action_label,
        "target_format": target_format,
        "status": status
    }
    await _request("post", "activities", headers=_headers(), json=data)
    await prune_old_activities()


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


async def get_user_lang_raw(user_id: int) -> str | None:
    result = await _request(
        "get",
        f"users?id=eq.{user_id}&select=language",
        headers=_headers()
    )
    if result and len(result) > 0 and result[0].get("language"):
        return result[0].get("language")
    return None


async def get_user_lang(user_id: int) -> str:
    lang = await get_user_lang_raw(user_id)
    return lang if lang in ["uz", "ru", "en"] else "uz"
