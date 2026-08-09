import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import save_user, get_user_lang, get_all_users_count, get_recent_activities
from bot.locales import MESSAGES
from keyboards.main_menu import get_main_menu
from bot.config import ADMIN_ID

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")
        ]
    ])
    await message.answer(MESSAGES["uz"]["welcome"], reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split(":")[1]
    try:
        await save_user(call.from_user.id, call.from_user.username, call.from_user.full_name, lang)
    except Exception as e:
        logger.error(f"Error saving user: {e}")

    await call.message.edit_text(
        f"✅ {'Til tanlandi!' if lang == 'uz' else 'Язык выбран!'}",
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


# Handle menu button presses
@router.message(F.text.in_(["📁 Konvertatsiya", "📁 Конвертация"]))
async def convert_menu(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(MESSAGES[lang]["send_file"])


@router.message(F.text.in_(["🌐 Til", "🌐 Язык"]))
async def lang_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")
        ]
    ])
    await message.answer("🌐 Tilni tanlang / Выберите язык:", reply_markup=kb)


@router.message(F.text.in_(["❓ Yordam", "❓ Помощь"]))
async def help_menu(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(MESSAGES[lang]["help_text"], parse_mode="HTML")
