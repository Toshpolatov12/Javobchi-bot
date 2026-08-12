import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.config import SNAKE_GAME_SHORT_NAME, GAME2048_SHORT_NAME, APP_URL

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.game_short_name)
async def game_callback_handler(call: CallbackQuery):
    game_short_name = call.game_short_name
    logger.info(f"Game callback received for: {game_short_name}")

    if game_short_name == SNAKE_GAME_SHORT_NAME:
        game_url = f"{APP_URL}/games/snake"
    elif game_short_name == GAME2048_SHORT_NAME:
        game_url = f"{APP_URL}/games/2048"
    else:
        game_url = f"{APP_URL}/games/snake"

    try:
        await call.answer(url=game_url)
    except Exception as e:
        logger.error(f"Error answering game callback query: {e}")
        await call.answer(text="⚠️ Could not launch game.", show_alert=True)
