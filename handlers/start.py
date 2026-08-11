import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.database import (
    save_user, get_user_lang, get_user_lang_raw,
    get_all_users_count, get_recent_activities
)
from bot.locales import MESSAGES
from keyboards.main_menu import get_main_menu, get_file_transfer_menu, get_language_keyboard
from bot.config import ADMIN_ID

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    saved_lang = await get_user_lang_raw(user_id)

    if saved_lang is None:
        # First time user: show language selection
        await message.answer(
            MESSAGES["uz"]["welcome_first"],
            reply_markup=get_language_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Existing user: show welcome back and main menu directly
        lang = saved_lang if saved_lang in ["uz", "ru", "en"] else "uz"
        await message.answer(
            MESSAGES[lang]["welcome_back"],
            reply_markup=get_main_menu(lang),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split(":")[1]
    if lang not in ["uz", "ru", "en"]:
        lang = "uz"

    try:
        await save_user(call.from_user.id, call.from_user.username, call.from_user.full_name, lang)
    except Exception as e:
        logger.error(f"Error saving user: {e}")

    await call.message.edit_text(
        MESSAGES[lang]["lang_changed"],
        parse_mode="HTML"
    )
    await call.message.answer(
        MESSAGES[lang]["main_menu"],
        reply_markup=get_main_menu(lang),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(Command("help"))
async def help_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(MESSAGES[lang]["help_text"], parse_mode="HTML")


@router.message(Command("stats"))
async def stats_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        users = await get_all_users_count()
        activities = await get_recent_activities(10)

        text = MESSAGES["uz"]["stats_text"].format(
            users=users,
            activities=len(activities)
        )

        if activities:
            text += "\n\n📋 <b>Oxirgi faollik:</b>\n"
            for act in activities[:10]:
                text += (
                    f"• {act.get('file_name', '?')} "
                    f"({act.get('action', '?')}) — "
                    f"{'✅' if act.get('status') == 'success' else '❌'}\n"
                )

        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"Error: {e}")


# --- Persistent Menu Button Handlers ---

# 🌐 Language Selection
@router.message(F.text.in_([
    "🌐 Til / Language",
    "🌐 Til", "🌐 Язык", "🌐 Language"
]))
async def lang_menu(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(
        MESSAGES[lang]["select_lang"],
        reply_markup=get_language_keyboard(),
        parse_mode="HTML"
    )


# 🤖 AI Mode
@router.message(F.text.in_([
    "🤖 AI rejim", "🤖 AI режим", "🤖 AI Mode",
    "🤖 AI Suhbat", "🤖 AI Чат"
]))
async def ai_menu(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(
        MESSAGES[lang]["ai_mode"],
        reply_markup=get_main_menu(lang),
        parse_mode="HTML"
    )


# 📁 File Transfer Section (Opens Submenu)
@router.message(F.text.in_([
    "📁 Fayl transfer", "📁 Конвертация файлов", "📁 File Transfer",
    "📁 Konvertatsiya", "📁 Конвертация"
]))
async def file_transfer_menu_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(
        MESSAGES[lang]["file_transfer_menu"],
        reply_markup=get_file_transfer_menu(lang),
        parse_mode="HTML"
    )


# ❓ Help (Inside File Transfer Submenu or Main Menu)
@router.message(F.text.in_([
    "❓ Yordam", "❓ Помощь", "❓ Help"
]))
async def help_menu(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(MESSAGES[lang]["help_text"], parse_mode="HTML")


# ⬅️ Back to Main Menu
@router.message(F.text.in_([
    "⬅️ Orqaga", "⬅️ Назад", "⬅️ Back"
]))
async def back_to_main_menu(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(
        MESSAGES[lang]["main_menu"],
        reply_markup=get_main_menu(lang),
        parse_mode="HTML"
    )
