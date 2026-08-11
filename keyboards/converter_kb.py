from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.locales import MESSAGES, FORMAT_DESCRIPTIONS


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


def build_format_descriptions_text(formats: list[str], lang: str) -> str:
    lines = []
    for ext in formats:
        emoji = _get_format_emoji(ext)
        desc = FORMAT_DESCRIPTIONS.get(ext.lower(), {}).get(lang, "")
        if desc:
            lines.append(f"• <b>{emoji} {ext.upper()}</b> — {desc}")
        else:
            lines.append(f"• <b>{emoji} {ext.upper()}</b>")
    return "\n".join(lines)


def _get_format_emoji(ext: str) -> str:
    emojis = {
        "jpg": "🖼", "jpeg": "🖼", "png": "🖼", "webp": "🖼",
        "bmp": "🖼", "tiff": "🖼", "ico": "🖼", "heic": "🖼",
        "pdf": "📕", "docx": "📘", "txt": "📝", "html": "🌐",
        "csv": "📊", "xlsx": "📗", "json": "💾", "xml": "📋",
        "yaml": "📋", "yml": "📋",
        "zip": "📦", "7z": "📦", "tar": "📦", "gz": "📦",
        "epub": "📚", "md": "📝",
        "mp3": "🎵", "ogg": "🎙", "wav": "🎧", "m4a": "🎶"
    }
    return emojis.get(ext.lower(), "📄")
