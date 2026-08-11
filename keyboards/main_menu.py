from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot.locales import MESSAGES


def get_main_menu(lang: str) -> ReplyKeyboardMarkup:
    msgs = MESSAGES.get(lang, MESSAGES["uz"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=msgs["btn_lang"]), KeyboardButton(text=msgs["btn_ai"])],
            [KeyboardButton(text=msgs["btn_converter"])]
        ],
        resize_keyboard=True
    )


def get_file_transfer_menu(lang: str) -> ReplyKeyboardMarkup:
    msgs = MESSAGES.get(lang, MESSAGES["uz"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=msgs["btn_help"]), KeyboardButton(text=msgs["btn_back"])]
        ],
        resize_keyboard=True
    )


def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
            ]
        ]
    )
