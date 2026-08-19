import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import BOT_TOKEN, get_all_bot_tokens

logger = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())
BOT_INSTANCES: dict[str, Bot] = {}
# Maps bot_id (numeric part before ':') -> full token
BOT_ID_TO_TOKEN: dict[str, str] = {}


def _extract_bot_id(token: str) -> str:
    """Extracts the numeric bot ID from a token like '896218801:AAEy...'"""
    return token.split(":")[0] if ":" in token else token


def get_bot_instance(token: str = None) -> Bot:
    """Returns or creates a Bot instance for the specified token."""
    tokens = get_all_bot_tokens()
    target_token = token if token else (tokens[0] if tokens else BOT_TOKEN)

    if not target_token:
        raise ValueError("No BOT_TOKEN or BOT_TOKENS provided in environment.")

    if target_token not in BOT_INSTANCES:
        try:
            BOT_INSTANCES[target_token] = Bot(token=target_token)
            bot_id = _extract_bot_id(target_token)
            BOT_ID_TO_TOKEN[bot_id] = target_token
            logger.info(f"Initialized Bot instance for bot_id: {bot_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Bot instance for token {target_token[:10]}...: {e}")
            raise e

    return BOT_INSTANCES[target_token]


def get_bot_by_id(bot_id: str = None) -> Bot | None:
    """Returns Bot instance by numeric bot_id or fallback to default."""
    if not bot_id:
        return get_bot_instance()

    token = BOT_ID_TO_TOKEN.get(bot_id)
    if token and token in BOT_INSTANCES:
        return BOT_INSTANCES[token]

    # Search through all configured tokens
    for t in get_all_bot_tokens():
        if _extract_bot_id(t) == bot_id:
            return get_bot_instance(t)

    return get_bot_instance()


def get_all_bots() -> list[Bot]:
    """Returns a list of Bot instances for all configured BOT_TOKENS."""
    bots = []
    for t in get_all_bot_tokens():
        try:
            b = get_bot_instance(t)
            bots.append(b)
        except Exception as e:
            logger.error(f"Skipping invalid bot token {t[:10]}...: {e}")
    return bots


# Initialize all bot instances at startup
for _token in get_all_bot_tokens():
    try:
        get_bot_instance(_token)
    except Exception as _e:
        logger.error(f"Startup: Failed to init bot {_token[:10]}...: {_e}")

# Default bot instance for backward compatibility
try:
    bot = get_bot_instance()
except Exception:
    bot = None
