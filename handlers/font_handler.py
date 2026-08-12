import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.font_engine import BUILTIN_FONTS, apply_font
from bot.database import get_user_lang, log_activity

logger = logging.getLogger(__name__)
router = Router()


def get_fonts_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    font_names = list(BUILTIN_FONTS.keys())
    row = []
    for name in font_names:
        row.append(InlineKeyboardButton(text=name, callback_data=f"font_select:{name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("font"))
async def font_command(message: Message):
    args = message.text.split(maxsplit=2)
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)

    if len(args) >= 3:
        style_input = args[1].title()
        text_to_format = args[2]

        if style_input in BUILTIN_FONTS:
            formatted = apply_font(style_input, text_to_format)
            await message.answer(f"✨ <b>{style_input}:</b>\n\n<code>{formatted}</code>", parse_mode="HTML")
            await log_activity(user_id, "font_style", f"{style_input}: {text_to_format}")
            return

    await message.answer(
        "🔤 <b>Matn Fontini Stilizatsiya Qilish</b>\n\n"
        "Kerakli font uslubini tanlang:",
        reply_markup=get_fonts_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("font_select:"))
async def font_select_callback(call: CallbackQuery):
    font_name = call.data.split(":")[1]
    sample_text = "Hello World 123"
    formatted = apply_font(font_name, sample_text)

    await call.message.edit_text(
        f"✨ <b>{font_name} Font:</b>\n\n"
        f"Namuna: <code>{formatted}</code>\n\n"
        f"💡 Foydalanish: <code>/font {font_name} Matningiz</code>",
        parse_mode="HTML",
        reply_markup=get_fonts_keyboard()
    )
    await call.answer()
