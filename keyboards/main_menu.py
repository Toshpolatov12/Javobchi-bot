from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.locales import MESSAGES

def get_main_menu(lang: str) -> ReplyKeyboardMarkup:
    msgs = MESSAGES.get(lang, MESSAGES["uz"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=msgs["convert_btn"]), KeyboardButton(text=msgs["ai_btn"])],
            [KeyboardButton(text=msgs["lang_btn"]), KeyboardButton(text=msgs["help_btn"])]
        ],
        resize_keyboard=True
    )
