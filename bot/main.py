import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import BOT_TOKEN, get_all_bot_tokens

logger = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())
BOT_INSTANCES: dict[str, Bot] = {}


def get_bot_instance(token: str = None) -> Bot:
    """Returns or creates a Bot instance for the specified token."""
    tokens = get_all_bot_tokens()
    target_token = token if token else (tokens[0] if tokens else BOT_TOKEN)

    if not target_token:
        raise ValueError("No BOT_TOKEN or BOT_TOKENS provided in environment.")

    if target_token not in BOT_INSTANCES:
        try:
            BOT_INSTANCES[target_token] = Bot(token=target_token)
            logger.info(f"Initialized Bot instance for token: {target_token[:10]}...")
        except Exception as e:
            logger.error(f"Failed to initialize Bot instance for token {target_token[:10]}...: {e}")
            raise e

    return BOT_INSTANCES[target_token]


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


# Default bot instance for backward compatibility
bot = get_bot_instance()
