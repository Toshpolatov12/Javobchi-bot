import logging
import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from bot.database import (
    is_admin, get_all_user_ids, is_maintenance_mode,
    set_maintenance_mode, add_admin, remove_admin, get_admins_list,
    ban_user, unban_user, get_all_users_count, get_recent_activities
)
from keyboards.admin_kb import (
    get_admin_main_kb, get_broadcast_confirm_kb, get_admin_back_kb
)

logger = logging.getLogger(__name__)
router = Router()


class AdminStates(StatesGroup):
    waiting_for_broadcast_msg = State()
    waiting_for_broadcast_confirm = State()
    waiting_for_new_admin = State()
    waiting_for_ban_user = State()
    waiting_for_unban_user = State()


# --- /admin Entry Point ---

@router.message(Command("admin"))
async def admin_panel_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_admin(user_id):
        return  # Silently ignore non-admins

    await state.clear()
    maintenance = await is_maintenance_mode()
    total_users = await get_all_users_count()

    text = (
        "👑 <b>Boshqaruv Paneli (Admin Dashboard)</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users} ta</b>\n"
        f"⚙️ Bot holati: <b>{'🔴 To\'xtatilgan (Uxlatilgan)' if maintenance else '🟢 Faol (Uyg\'oq)'}</b>\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=get_admin_main_kb(maintenance), parse_mode="HTML")


@router.callback_query(F.data == "admin:menu")
async def admin_menu_callback(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    await state.clear()
    maintenance = await is_maintenance_mode()
    total_users = await get_all_users_count()

    text = (
        "👑 <b>Boshqaruv Paneli (Admin Dashboard)</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users} ta</b>\n"
        f"⚙️ Bot holati: <b>{'🔴 To\'xtatilgan (Uxlatilgan)' if maintenance else '🟢 Faol (Uyg\'oq)'}</b>\n\n"
        "Kerakli bo'limni tanlang:"
    )
    try:
        await call.message.edit_text(text, reply_markup=get_admin_main_kb(maintenance), parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=get_admin_main_kb(maintenance), parse_mode="HTML")
    await call.answer()


# --- Maintenance / Sleep Toggle ---

@router.callback_query(F.data == "admin:toggle_maintenance")
async def toggle_maintenance_handler(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    current = await is_maintenance_mode()
    new_status = not current
    await set_maintenance_mode(new_status)

    alert_text = "🔴 Bot to'xtatildi (uxlatildi)!" if new_status else "🟢 Bot ishga tushirildi (uyg'otildi)!"
    await call.answer(alert_text, show_alert=True)

    total_users = await get_all_users_count()
    text = (
        "👑 <b>Boshqaruv Paneli (Admin Dashboard)</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users} ta</b>\n"
        f"⚙️ Bot holati: <b>{'🔴 To\'xtatilgan (Uxlatilgan)' if new_status else '🟢 Faol (Uyg\'oq)'}</b>\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await call.message.edit_text(text, reply_markup=get_admin_main_kb(new_status), parse_mode="HTML")


@router.callback_query(F.data == "admin:status_info")
async def status_info_handler(call: CallbackQuery):
    m = await is_maintenance_mode()
    st = "🔴 Bot hozir to'xtatilgan (faqat adminlar uchun ishlaydi)" if m else "🟢 Bot barcha foydalanuvchilar uchun faol"
    await call.answer(st, show_alert=True)


# --- Broadcast (Xabar Tarqatish) ---

@router.callback_query(F.data == "admin:broadcast")
async def start_broadcast_flow(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_broadcast_msg)
    text = (
        "📢 <b>Xabar tarqatish bo'limi</b>\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring (matn, rasm, video, audio yoki forward post).\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing yoki pastdagi tugmani bosing.</i>"
    )
    await call.message.edit_text(text, reply_markup=get_admin_back_kb(), parse_mode="HTML")
    await call.answer()


@router.message(AdminStates.waiting_for_broadcast_msg)
async def receive_broadcast_message(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Xabar tarqatish bekor qilindi.", reply_markup=get_admin_back_kb())
        return

    # Store message details in state
    await state.update_data(
        chat_id=message.chat.id,
        message_id=message.message_id
    )
    await state.set_state(AdminStates.waiting_for_broadcast_confirm)

    await message.answer(
        "👁 <b>Xabar qabul qilindi!</b>\n\n"
        "Qanday rejimda yuborilsin?",
        reply_markup=get_broadcast_confirm_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.in_(["bcast:send_sound", "bcast:send_silent"]), AdminStates.waiting_for_broadcast_confirm)
async def execute_broadcast(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    is_silent = (call.data == "bcast:send_silent")
    data = await state.get_data()
    from_chat_id = data.get("chat_id")
    from_message_id = data.get("message_id")
    await state.clear()

    user_ids = await get_all_user_ids()
    if not user_ids:
        await call.message.edit_text("❌ Bazada foydalanuvchilar topilmadi.", reply_markup=get_admin_back_kb())
        return

    status_msg = await call.message.edit_text(
        f"⏳ <b>Xabar tarqatilmoqda...</b>\n\n"
        f"Rejim: <b>{'🔕 Ovozsiz (Jim)' if is_silent else '🔊 Ovozli (Bildirishnoma bilan)'}</b>\n"
        f"Jami foydalanuvchilar: <b>{len(user_ids)} ta</b>\n"
        f"Iltimos kuting...",
        parse_mode="HTML"
    )

    sent_count = 0
    blocked_count = 0
    failed_count = 0

    target_bot = call.bot

    for uid in user_ids:
        try:
            await target_bot.copy_message(
                chat_id=uid,
                from_chat_id=from_chat_id,
                message_id=from_message_id,
                disable_notification=is_silent
            )
            sent_count += 1
        except TelegramForbiddenError:
            blocked_count += 1
        except TelegramBadRequest as e:
            if "blocked" in str(e).lower() or "not found" in str(e).lower():
                blocked_count += 1
            else:
                failed_count += 1
        except Exception:
            failed_count += 1

        # Safe rate limit (~25 messages/sec)
        await asyncio.sleep(0.04)

    report = (
        "✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"📢 Rejim: <b>{'🔕 Ovozsiz' if is_silent else '🔊 Ovozli'}</b>\n"
        f"👥 Jami qabul qiluvchilar: <b>{len(user_ids)} ta</b>\n"
        f"✅ Muvaffaqiyatli yetkazildi: <b>{sent_count} ta</b>\n"
        f"🚫 Botni bloklaganlar: <b>{blocked_count} ta</b>\n"
        f"❌ Xatoliklar: <b>{failed_count} ta</b>"
    )
    await status_msg.edit_text(report, reply_markup=get_admin_back_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "bcast:cancel")
async def cancel_broadcast(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Xabar tarqatish bekor qilindi.", reply_markup=get_admin_back_kb())
    await call.answer()


# --- Multi-Admin Management ---

@router.callback_query(F.data == "admin:list_admins")
async def list_admins_handler(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    admins = await get_admins_list()
    text = "👥 <b>Adminlar ro'yxati:</b>\n\n"
    text += f"👑 <b>SuperAdmin:</b> <code>{call.from_user.id}</code> (Siz)\n\n"

    if admins:
        text += "📋 <b>Qo'shilgan adminlar:</b>\n"
        for adm in admins:
            uname = f"(@{adm.get('username')})" if adm.get("username") else ""
            text += f"• ID: <code>{adm.get('id')}</code> {uname} — <i>{adm.get('role', 'admin')}</i>\n"
    else:
        text += "<i>Hozircha qo'shimcha adminlar yo'q.</i>"

    await call.message.edit_text(text, reply_markup=get_admin_back_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin:add_admin")
async def add_admin_prompt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_new_admin)
    text = (
        "➕ <b>Yangi admin qo'shish</b>\n\n"
        "Yangi admin qilmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b> raqamini yuboring:\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await call.message.edit_text(text, reply_markup=get_admin_back_kb(), parse_mode="HTML")
    await call.answer()


@router.message(AdminStates.waiting_for_new_admin)
async def process_new_admin(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=get_admin_back_kb())
        return

    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamli Telegram ID kiriting:")
        return

    new_admin_id = int(raw)
    success = await add_admin(new_admin_id, added_by=message.from_user.id)
    await state.clear()

    if success:
        await message.answer(f"✅ Foydalanuvchi <code>{new_admin_id}</code> muvaffaqiyatli admin qilindi!", reply_markup=get_admin_back_kb(), parse_mode="HTML")
    else:
        await message.answer("❌ Admin qo'shishda xatolik yuz berdi.", reply_markup=get_admin_back_kb())


# --- Ban / Unban Management ---

@router.callback_query(F.data == "admin:ban_user")
async def ban_user_prompt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_ban_user)
    await call.message.edit_text("🚫 <b>Foydalanuvchini bloklash (Ban)</b>\n\nBloklamoqchi bo'lgan foydalanuvchining <b>Telegram ID</b> raqamini yuboring:", reply_markup=get_admin_back_kb(), parse_mode="HTML")
    await call.answer()


@router.message(AdminStates.waiting_for_ban_user)
async def process_ban_user(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=get_admin_back_kb())
        return

    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamli Telegram ID kiriting:")
        return

    target_id = int(raw)
    await ban_user(target_id, reason="Admin tomonidan bloklandi")
    await state.clear()
    await message.answer(f"🚫 Foydalanuvchi <code>{target_id}</code> botdan bloklandi!", reply_markup=get_admin_back_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin:unban_user")
async def unban_user_prompt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_unban_user)
    await call.message.edit_text("✅ <b>Foydalanuvchini bandan olish (Unban)</b>\n\nBandan chiqarmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b> raqamini yuboring:", reply_markup=get_admin_back_kb(), parse_mode="HTML")
    await call.answer()


@router.message(AdminStates.waiting_for_unban_user)
async def process_unban_user(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=get_admin_back_kb())
        return

    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamli Telegram ID kiriting:")
        return

    target_id = int(raw)
    await unban_user(target_id)
    await state.clear()
    await message.answer(f"✅ Foydalanuvchi <code>{target_id}</code> blokdan chiqarildi!", reply_markup=get_admin_back_kb(), parse_mode="HTML")


# --- Stats in Admin Panel ---

@router.callback_query(F.data == "admin:stats")
async def admin_stats_callback(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    users = await get_all_users_count()
    activities = await get_recent_activities(15)

    text = (
        f"📊 <b>Kengaytirilgan Bot Statistikasi</b>\n\n"
        f"👥 Jami ro'yxatdan o'tganlar: <b>{users} ta</b>\n"
        f"📁 Oxirgi faolliklar soni: <b>{len(activities)} ta</b>\n\n"
    )
    if activities:
        text += "📋 <b>So'nggi operatsiyalar:</b>\n"
        for act in activities[:10]:
            status_emoji = "✅" if act.get("status") == "success" else "❌"
            text += f"• {act.get('file_name', '?')[:25]} ({act.get('action', '?')}) — {status_emoji}\n"

    await call.message.edit_text(text, reply_markup=get_admin_back_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin:close")
async def admin_close_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.delete()
    except Exception:
        await call.message.edit_text("🔒 Admin panel yopildi.")
    await call.answer()
