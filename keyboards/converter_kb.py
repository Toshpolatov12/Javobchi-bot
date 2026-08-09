from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.locales import MESSAGES


def get_format_keyboard(formats: list[str], lang: str) -> InlineKeyboardMarkup:
    msgs = MESSAGES.get(lang, MESSAGES["uz"])

    buttons = []
    row = []
    for ext in formats:
        emoji = _get_format_emoji(ext)
        row.append(InlineKeyboardButton(
            text=f"{emoji} {ext.upper()}",
            callback_data=f"cvt:{ext}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(
        text=f"❌ {msgs['cancel']}",
        callback_data="cancel_cvt"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _get_format_emoji(ext: str) -> str:
    emojis = {
        "jpg": "🖼", "jpeg": "🖼", "png": "🖼", "webp": "🖼",
        "bmp": "🖼", "tiff": "🖼", "ico": "🖼",
        "pdf": "📕", "docx": "📘", "txt": "📝", "html": "🌐",
        "csv": "📊", "xlsx": "📗", "json": "💾", "xml": "📋",
        "yaml": "📋", "yml": "📋",
        "zip": "📦", "7z": "📦", "tar": "📦", "gz": "📦",
        "epub": "📚", "md": "📝",
    }
    return emojis.get(ext.lower(), "📄")
