import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.config import SNAKE_GAME_SHORT_NAME, GAME2048_SHORT_NAME, APP_URL
from bot.database import log_activity

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.game_short_name)
async def game_callback_handler(call: CallbackQuery):
    game_short_name = call.game_short_name
    user_id = call.from_user.id
    logger.info(f"Game callback received for: {game_short_name} from user {user_id}")

    if game_short_name == SNAKE_GAME_SHORT_NAME:
        game_url = f"{APP_URL}/games/snake"
    elif game_short_name == GAME2048_SHORT_NAME:
        game_url = f"{APP_URL}/games/2048"
    else:
        game_url = f"{APP_URL}/games/snake"

    try:
        await call.answer(url=game_url)
        await log_activity(user_id, "game_played", game_short_name, "success")
    except Exception as e:
        logger.error(f"Error answering game callback query: {e}")
        await call.answer(text="⚠️ Could not launch game.", show_alert=True)
        await log_activity(user_id, "game_played", game_short_name, f"error: {str(e)[:50]}")
