import time
import logging
from bot.config import GEMINI_API_KEY, GROQ_API_KEY

logger = logging.getLogger(__name__)

BUSY_COOLDOWN_SECONDS = 60


class KeyRotator:
    def __init__(self, keys_raw: str):
        if keys_raw:
            self.keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
        else:
            self.keys = []
        self._busy_until: dict[int, float] = {}
        self._current_index = 0

    def is_empty(self) -> bool:
        return len(self.keys) == 0

    def _is_busy(self, index: int) -> bool:
        until = self._busy_until.get(index)
        if until is None:
            return False
        if time.time() >= until:
            del self._busy_until[index]
            return False
        return True

    def get_key(self) -> str | None:
        if not self.keys:
            return None

        # Check for non-busy key
        for i in range(len(self.keys)):
            idx = (self._current_index + i) % len(self.keys)
            if not self._is_busy(idx):
                self._current_index = idx
                return self.keys[idx]

        # If all busy, return earliest expiring
        soonest = min(range(len(self.keys)), key=lambda i: self._busy_until.get(i, 0))
        self._current_index = soonest
        return self.keys[soonest]

    def mark_busy(self):
        if self.keys:
            logger.warning(f"Key index {self._current_index} hit rate limit / 429. Rotating to next key...")
            self._busy_until[self._current_index] = time.time() + BUSY_COOLDOWN_SECONDS
            self._current_index = (self._current_index + 1) % len(self.keys)


# --- Smart key detection ---
# Collect all Groq keys (start with "gsk_") from both env vars
# Collect all Gemini keys (do NOT start with "gsk_") from both env vars
_all_raw_keys = []
if GROQ_API_KEY:
    _all_raw_keys.extend([k.strip() for k in GROQ_API_KEY.split(",") if k.strip()])
if GEMINI_API_KEY:
    _all_raw_keys.extend([k.strip() for k in GEMINI_API_KEY.split(",") if k.strip()])

_groq_keys = [k for k in _all_raw_keys if k.startswith("gsk_")]
_gemini_keys = [k for k in _all_raw_keys if not k.startswith("gsk_")]

# Remove duplicates while preserving order
_seen = set()
_groq_unique = []
for k in _groq_keys:
    if k not in _seen:
        _seen.add(k)
        _groq_unique.append(k)
_gemini_unique = []
for k in _gemini_keys:
    if k not in _seen:
        _seen.add(k)
        _gemini_unique.append(k)

groq_rotator = KeyRotator(",".join(_groq_unique) if _groq_unique else "")
gemini_rotator = KeyRotator(",".join(_gemini_unique) if _gemini_unique else "")

logger.info(f"AI Keys loaded: {len(_groq_unique)} Groq key(s), {len(_gemini_unique)} Gemini key(s)")
