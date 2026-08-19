from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_kb(maintenance_enabled: bool = False) -> InlineKeyboardMarkup:
    status_icon = "🟢 Faol (Uyg'oq)" if not maintenance_enabled else "🔴 To'xtatilgan (Uxlatilgan)"
    toggle_text = "⏸ Botni to'xtatish (Uxlatish)" if not maintenance_enabled else "▶️ Botni ishga tushirish (Uyg'otish)"

    buttons = [
        [
            InlineKeyboardButton(text="📢 Xabar tarqatish (Post yuborish)", callback_data="admin:broadcast")
        ],
        [
            InlineKeyboardButton(text=f"⚙️ Holat: {status_icon}", callback_data="admin:status_info"),
        ],
        [
            InlineKeyboardButton(text=toggle_text, callback_data="admin:toggle_maintenance")
        ],
        [
            InlineKeyboardButton(text="👥 Adminlar", callback_data="admin:list_admins"),
            InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin:add_admin")
        ],
        [
            InlineKeyboardButton(text="🚫 Ban qilish", callback_data="admin:ban_user"),
            InlineKeyboardButton(text="✅ Bandan olish", callback_data="admin:unban_user")
        ],
        [
            InlineKeyboardButton(text="📊 Jonli statistika", callback_data="admin:stats")
        ],
        [
            InlineKeyboardButton(text="❌ Yopish", callback_data="admin:close")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🔊 Ovozli yuborish (Bildirishnoma bilan)", callback_data="bcast:send_sound"),
        ],
        [
            InlineKeyboardButton(text="🔕 Ovozsiz yuborish (Jim rejimda)", callback_data="bcast:send_silent"),
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bcast:cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin:menu")
    ]])
