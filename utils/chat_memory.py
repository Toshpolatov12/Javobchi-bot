import logging
import time
from bot.database import _request, _headers

logger = logging.getLogger(__name__)

# Maximum conversation turns (user + assistant messages) to keep in memory per user
MAX_HISTORY_MESSAGES = 10
# Inactivity timeout (clear memory if no message for 2 hours)
SESSION_TIMEOUT_SECONDS = 7200

# In-memory storage: user_id -> {"last_active": timestamp, "messages": [{"role": "user"|"assistant", "content": str}]}
_MEMORY_STORE: dict[int, dict] = {}


async def get_user_history(user_id: int) -> list[dict]:
    """
    Returns the recent conversation history for the user as a list of:
    [{"role": "user"|"assistant", "content": "..."}]
    """
    # 1. Check in-memory store
    user_session = _MEMORY_STORE.get(user_id)
    if user_session:
        # Check session expiry
        if time.time() - user_session.get("last_active", 0) > SESSION_TIMEOUT_SECONDS:
            _MEMORY_STORE.pop(user_id, None)
            return []
        return list(user_session.get("messages", []))

    # 2. Try loading from Supabase (if available)
    try:
        data = await _request(
            "get",
            f"chat_history?user_id=eq.{user_id}&order=id.desc&limit={MAX_HISTORY_MESSAGES}",
            headers=_headers()
        )
        if data and isinstance(data, list):
            # Reverse because we queried DESC
            history = [{"role": r["role"], "content": r["content"]} for r in reversed(data)]
            _MEMORY_STORE[user_id] = {
                "last_active": time.time(),
                "messages": history
            }
            return history
    except Exception as e:
        logger.debug(f"Could not load chat history from Supabase: {e}")

    return []


async def add_chat_turn(user_id: int, user_text: str, ai_text: str):
    """
    Appends a user message and AI response pair to both memory and Supabase.
    """
    # Update in-memory
    if user_id not in _MEMORY_STORE:
        _MEMORY_STORE[user_id] = {
            "last_active": time.time(),
            "messages": []
        }

    session = _MEMORY_STORE[user_id]
    session["last_active"] = time.time()
    session["messages"].append({"role": "user", "content": user_text})
    session["messages"].append({"role": "assistant", "content": ai_text})

    # Trim to MAX_HISTORY_MESSAGES
    if len(session["messages"]) > MAX_HISTORY_MESSAGES:
        session["messages"] = session["messages"][-MAX_HISTORY_MESSAGES:]

    # Persist to Supabase asynchronously (best effort)
    try:
        rows = [
            {"user_id": user_id, "role": "user", "content": user_text[:2000]},
            {"user_id": user_id, "role": "assistant", "content": ai_text[:4000]}
        ]
        await _request("post", "chat_history", headers=_headers(), json=rows)
    except Exception as e:
        logger.debug(f"Could not save chat turn to Supabase: {e}")


async def clear_user_history(user_id: int):
    """
    Clears the conversation context for the user (starts a new topic/chat).
    """
    _MEMORY_STORE.pop(user_id, None)
    try:
        await _request("delete", f"chat_history?user_id=eq.{user_id}", headers=_headers())
    except Exception as e:
        logger.debug(f"Could not delete chat history from Supabase: {e}")
