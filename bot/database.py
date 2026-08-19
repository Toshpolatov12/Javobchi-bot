import logging
import time
import httpx
from bot.config import SUPABASE_URL, SUPABASE_KEY, ADMIN_ID

logger = logging.getLogger(__name__)

MAX_ACTIVITY_LOGS = 2000  # FIFO Pruning limit to keep Supabase storage free & safe

# In-memory caches for high-speed checks (prevents DB overhead on every message)
_ADMIN_CACHE: dict[int, bool] = {}
_BAN_CACHE: dict[int, bool] = {}
_MAINTENANCE_STATUS: dict[str, any] = {"enabled": False, "last_checked": 0}


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


async def get_all_user_ids() -> list[int]:
    """Returns a list of all user IDs in the database for broadcasting."""
    try:
        result = await _request("get", "users?select=id", headers=_headers())
        if result and isinstance(result, list):
            return [int(r["id"]) for r in result if "id" in r]
    except Exception as e:
        logger.error(f"Error fetching all user IDs: {e}")
    return []


# --- Multi-Admin Management ---

async def is_admin(user_id: int) -> bool:
    """Checks if user is SuperAdmin (ADMIN_ID) or in admins table."""
    if ADMIN_ID and user_id == ADMIN_ID:
        return True

    # Check cache
    if user_id in _ADMIN_CACHE:
        return _ADMIN_CACHE[user_id]

    try:
        res = await _request("get", f"admins?id=eq.{user_id}&select=id", headers=_headers())
        is_adm = bool(res and len(res) > 0)
        _ADMIN_CACHE[user_id] = is_adm
        return is_adm
    except Exception:
        return False


async def add_admin(user_id: int, username: str = "", role: str = "admin", added_by: int = 0) -> bool:
    try:
        data = {
            "id": user_id,
            "username": username or "",
            "role": role,
            "added_by": added_by
        }
        res = await _request("post", "admins", headers=_headers("resolution=merge-duplicates"), json=data)
        _ADMIN_CACHE[user_id] = True
        return res is not None
    except Exception as e:
        logger.error(f"Error adding admin {user_id}: {e}")
        return False


async def remove_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return False  # Cannot remove superadmin
    try:
        await _request("delete", f"admins?id=eq.{user_id}", headers=_headers())
        _ADMIN_CACHE.pop(user_id, None)
        return True
    except Exception as e:
        logger.error(f"Error removing admin {user_id}: {e}")
        return False


async def get_admins_list() -> list[dict]:
    try:
        res = await _request("get", "admins?select=*&order=created_at.desc", headers=_headers())
        return res if isinstance(res, list) else []
    except Exception as e:
        logger.error(f"Error getting admins list: {e}")
        return []


# --- Maintenance / Sleep Mode ---

async def is_maintenance_mode() -> bool:
    """Returns True if bot is in maintenance mode (sleep/pause)."""
    now = time.time()
    if now - _MAINTENANCE_STATUS["last_checked"] < 30:
        return _MAINTENANCE_STATUS["enabled"]

    try:
        res = await _request("get", "bot_settings?key=eq.maintenance&select=value", headers=_headers())
        if res and len(res) > 0:
            val = str(res[0].get("value", "false")).lower() == "true"
            _MAINTENANCE_STATUS["enabled"] = val
            _MAINTENANCE_STATUS["last_checked"] = now
            return val
    except Exception:
        pass
    return _MAINTENANCE_STATUS["enabled"]


async def set_maintenance_mode(enabled: bool) -> bool:
    try:
        data = {
            "key": "maintenance",
            "value": "true" if enabled else "false"
        }
        await _request("post", "bot_settings", headers=_headers("resolution=merge-duplicates"), json=data)
        _MAINTENANCE_STATUS["enabled"] = enabled
        _MAINTENANCE_STATUS["last_checked"] = time.time()
        return True
    except Exception as e:
        logger.error(f"Error setting maintenance mode: {e}")
        _MAINTENANCE_STATUS["enabled"] = enabled
        return False


# --- User Ban Management ---

async def is_user_banned(user_id: int) -> bool:
    if user_id in _BAN_CACHE:
        return _BAN_CACHE[user_id]
    try:
        res = await _request("get", f"banned_users?id=eq.{user_id}&select=id", headers=_headers())
        banned = bool(res and len(res) > 0)
        _BAN_CACHE[user_id] = banned
        return banned
    except Exception:
        return False


async def ban_user(user_id: int, reason: str = "") -> bool:
    try:
        data = {"id": user_id, "reason": reason}
        await _request("post", "banned_users", headers=_headers("resolution=merge-duplicates"), json=data)
        _BAN_CACHE[user_id] = True
        return True
    except Exception as e:
        logger.error(f"Error banning user {user_id}: {e}")
        return False


async def unban_user(user_id: int) -> bool:
    try:
        await _request("delete", f"banned_users?id=eq.{user_id}", headers=_headers())
        _BAN_CACHE[user_id] = False
        return True
    except Exception as e:
        logger.error(f"Error unbanning user {user_id}: {e}")
        return False


# --- Activity & Logging ---

async def prune_old_activities(max_rows: int = MAX_ACTIVITY_LOGS):
    try:
        result = await _request("get", "activities?select=id&order=id.asc", headers=_headers())
        if result and isinstance(result, list) and len(result) > max_rows:
            overflow = len(result) - max_rows
            ids_to_delete = [str(r["id"]) for r in result[:overflow] if "id" in r]
            if ids_to_delete:
                ids_str = ",".join(ids_to_delete)
                await _request("delete", f"activities?id=in.({ids_str})", headers=_headers())
    except Exception as e:
        logger.error(f"Error during Supabase activity log pruning: {e}")


async def log_activity(user_id: int, action_type: str, content: str, status: str = "success", bot_username: str = ""):
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
    result = await _request("get", f"activities?user_id=eq.{user_id}&select=id", headers=_headers())
    return len(result) if result else 0


async def get_all_users_count() -> int:
    result = await _request("get", "users?select=id", headers=_headers())
    return len(result) if result else 0


async def get_recent_activities(limit: int = 50) -> list:
    result = await _request("get", f"activities?select=*&order=created_at.desc&limit={limit}", headers=_headers())
    return result if result else []


async def get_user_lang_raw(user_id: int) -> str | None:
    result = await _request("get", f"users?id=eq.{user_id}&select=language", headers=_headers())
    if result and len(result) > 0 and result[0].get("language"):
        return result[0].get("language")
    return None


async def get_user_lang(user_id: int) -> str:
    lang = await get_user_lang_raw(user_id)
    return lang if lang in ["uz", "ru", "en"] else "uz"
