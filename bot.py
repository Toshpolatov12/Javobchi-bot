import logging
import json
from datetime import datetime
import asyncio
import aiohttp
import base64
import os
import qrcode
import io
from gtts import gTTS
from fpdf import FPDF
from PIL import Image
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CHANNEL = "@uzinnotech"

# ✅ FIX #6: ADMIN_ID env dan olinadi
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7189342638"))

# ✅ FIX #1: JSON fayl orqali persistent storage
DB_FILE = "users_db.json"

def load_users_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users_db(db: dict):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"DB saqlash xatosi: {e}")

users_db = load_users_db()

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

class UserState(StatesGroup):
    choosing_language = State()
    main_menu = State()
    ai_chat = State()
    qr_waiting = State()
    pdf_waiting = State()
    tts_waiting = State()

TEXTS = {
    "uz": {
        "subscribe_msg": (
            "⚠️ Botdan foydalanish uchun kanalga obuna bo'lishingiz kerak!\n\n"
            "👇 Quyidagi tugmani bosib kanalga o'ting va obuna bo'ling:"
        ),
        "subscribe_channel_btn": "📢 Kanalga o'tish",
        "subscribe_check": "✅ Obuna bo'ldim",
        "subscribe_error": "❌ Siz hali obuna bo'lmagansiz!\n\nIltimos, avval kanalga obuna bo'ling 👇",
        "subscribe_success": "✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.",
        "unsubscribed_msg": (
            "⚠️ Siz kanaldan chiqib ketgansiz!\n\n"
            "Botdan foydalanishni davom ettirish uchun yana obuna bo'lishingiz kerak 👇"
        ),
        "welcome": (
            "👋 Salom! Men AI Javobchi botman!\n\n"
            "📌 Quyidagi tugmalardan birini tanlang.\n\n"
            "💡 Bot haqida savol bersangiz, javob beraman!"
        ),
        "ai_btn": "🤖 AI Assistant",
        "qr_btn": "📷 QR Kod yaratuvchi",
        "pdf_btn": "📄 PDF Generator",
        "tts_btn": "🎙 Matnni ovozga aylantirish",
        "back_btn": "🔙 Orqaga",
        "thinking": "🤔 O'ylamoqda...",
        "ai_welcome": "🤖 AI Assistant yoqildi!\nIstalgan savolingizni yozing.\n\n(Orqaga: 🔙 Orqaga)",
        "qr_prompt": "📷 Matn yoki link yuboring, QR kodga aylantirib beraman!\n\n(Orqaga: 🔙 Orqaga)",
        "qr_uploading": "⏳ Fayl yuklanmoqda...",
        "qr_success": "✅ QR kod tayyor!",
        "qr_error": "❌ Xatolik yuz berdi.",
        "pdf_prompt": "📄 Matningizni yuboring, PDF ga aylantirib beraman!\n\n(Orqaga: 🔙 Orqaga)",
        "pdf_success": "✅ PDF tayyor!",
        "pdf_error": "❌ PDF yaratishda xatolik.",
        "pdf_processing": "⏳ PDF yaratilmoqda...",
        "tts_prompt": "🎙 Matnni yuboring, ovozga aylantirib beraman!\n\n(Orqaga: 🔙 Orqaga)",
        "tts_processing": "⏳ Ovoz yaratilmoqda...",
        "tts_success": "✅ Ovoz tayyor!",
        "tts_error": "❌ Ovoz yaratishda xatolik.",
        "bot_system": (
            "Sen AI Javobchi botsаn. "
            "Foydalanuvchi faqat bot haqida savol berishi mumkin. "
            "Bot nima qila olishi: AI bilan suhbat, QR kod yaratish (rasm QR ichiga joylanadi), PDF yaratish, matnni ovozga aylantirish. "
            "AI funksiyasi haqida so'ralsa: AI Assistant aqlli suhbat qura oladi, suhbat davomida oxirgi 20 ta xabarni eslab qoladi, "
            "ya'ni oldingi savollar va javoblar asosida muomala qiladi. Orqaga tugmasi bosilganda esa suhbat tarixi tozalanadi va yangi suhbat boshlanadi. "
            "Bot yaratuvchisi haqida hech qanday ma'lumot berma. "
            "Boshqa savollarga: 'Bosh sahifada faqat bot haqidagi ma'lumotlarni bilib olishingiz mumkin. "
            "AI Assistant tugmasini bosing!' deb javob ber. O'zbek tilida gapir."
        ),
    },
    "ru": {
        "subscribe_msg": (
            "⚠️ Для использования бота нужно подписаться на канал!\n\n"
            "👇 Нажмите кнопку ниже и подпишитесь:"
        ),
        "subscribe_channel_btn": "📢 Перейти на канал",
        "subscribe_check": "✅ Я подписался",
        "subscribe_error": "❌ Вы ещё не подписались!\n\nПожалуйста, сначала подпишитесь на канал 👇",
        "subscribe_success": "✅ Подписка подтверждена! Можете пользоваться ботом.",
        "unsubscribed_msg": (
            "⚠️ Вы отписались от канала!\n\n"
            "Чтобы продолжить использование бота, необходимо снова подписаться 👇"
        ),
        "welcome": (
            "👋 Привет! Я AI Javobchi бот!\n\n"
            "📌 Выберите одну из кнопок ниже.\n\n"
            "💡 Можете задать вопрос о боте!"
        ),
        "ai_btn": "🤖 AI Assistant",
        "qr_btn": "📷 QR Код генератор",
        "pdf_btn": "📄 PDF Генератор",
        "tts_btn": "🎙 Текст в голос",
        "back_btn": "🔙 Назад",
        "thinking": "🤔 Думаю...",
        "ai_welcome": "🤖 AI Assistant включён!\nЗадайте любой вопрос.\n\n(Назад: 🔙 Назад)",
        "qr_prompt": "📷 Отправьте текст или ссылку, преобразую в QR код!\n\n(Назад: 🔙 Назад)",
        "qr_uploading": "⏳ Загрузка файла...",
        "qr_success": "✅ QR код готов!",
        "qr_error": "❌ Произошла ошибка.",
        "pdf_prompt": "📄 Отправьте текст, преобразую в PDF!\n\n(Назад: 🔙 Назад)",
        "pdf_success": "✅ PDF готов!",
        "pdf_error": "❌ Ошибка при создании PDF.",
        "pdf_processing": "⏳ Создаю PDF...",
        "tts_prompt": "🎙 Отправьте текст, преобразую в голос!\n\n(Назад: 🔙 Назад)",
        "tts_processing": "⏳ Создаю аудио...",
        "tts_success": "✅ Аудио готово!",
        "tts_error": "❌ Ошибка при создании аудио.",
        "bot_system": (
            "Ты бот AI Javobchi. "
            "Пользователь может спрашивать только о боте. "
            "Что умеет бот: AI чат, создание QR кода (изображение помещается в QR), создание PDF, преобразование текста в голос. "
            "Если спросят об AI функции: AI Assistant умеет вести умный диалог, запоминает последние 20 сообщений в разговоре, "
            "то есть отвечает с учётом предыдущих вопросов и ответов. При нажатии кнопки 'Назад' история разговора очищается и начинается заново. "
            "Никогда не раскрывай информацию о создателе бота. "
            "На другие вопросы: 'На главной странице только о боте. Нажмите AI Assistant!' Говори по-русски."
        ),
    },
    "en": {
        "subscribe_msg": (
            "⚠️ You need to subscribe to our channel to use this bot!\n\n"
            "👇 Click the button below to subscribe:"
        ),
        "subscribe_channel_btn": "📢 Go to Channel",
        "subscribe_check": "✅ I subscribed",
        "subscribe_error": "❌ You haven't subscribed yet!\n\nPlease subscribe to the channel first 👇",
        "subscribe_success": "✅ Subscription confirmed! You can use the bot now.",
        "unsubscribed_msg": (
            "⚠️ You have left the channel!\n\n"
            "To continue using the bot, you need to subscribe again 👇"
        ),
        "welcome": (
            "👋 Hello! I'm AI Javobchi bot!\n\n"
            "📌 Choose one of the buttons below.\n\n"
            "💡 You can ask questions about the bot!"
        ),
        "ai_btn": "🤖 AI Assistant",
        "qr_btn": "📷 QR Code Creator",
        "pdf_btn": "📄 PDF Generator",
        "tts_btn": "🎙 Text to Speech",
        "back_btn": "🔙 Back",
        "thinking": "🤔 Thinking...",
        "ai_welcome": "🤖 AI Assistant activated!\nAsk me anything.\n\n(Back: 🔙 Back)",
        "qr_prompt": "📷 Send text or a link, I'll convert it to a QR code!\n\n(Back: 🔙 Back)",
        "qr_uploading": "⏳ Uploading file...",
        "qr_success": "✅ QR code ready!",
        "qr_error": "❌ An error occurred.",
        "pdf_prompt": "📄 Send text and I'll convert it to PDF!\n\n(Back: 🔙 Back)",
        "pdf_success": "✅ PDF ready!",
        "pdf_error": "❌ Error creating PDF.",
        "pdf_processing": "⏳ Creating PDF...",
        "tts_prompt": "🎙 Send text and I'll convert it to voice!\n\n(Back: 🔙 Back)",
        "tts_processing": "⏳ Creating audio...",
        "tts_success": "✅ Audio ready!",
        "tts_error": "❌ Error creating audio.",
        "bot_system": (
            "You are AI Javobchi bot. "
            "User can only ask about the bot. "
            "Bot features: AI chat, QR code (image embedded in QR), PDF, text to speech. "
            "If asked about the AI feature: AI Assistant can hold smart conversations and remembers the last 20 messages, "
            "meaning it responds based on previous questions and answers. When the 'Back' button is pressed, the conversation history is cleared and a new chat begins. "
            "Never reveal information about the bot's creator. "
            "For other questions: 'On main page you can only learn about the bot. Press AI Assistant!' Speak English."
        ),
    }
}

# ✅ FIX #3: Obuna tekshiruvida xato bo'lsa True qaytaradi (bloklamaydi)
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status not in ["left", "kicked", "banned"]
    except Exception as e:
        logging.error(f"Obuna tekshirish xatosi: {e}")
        return True  # ✅ Xato bo'lsa, foydalanuvchini bloklamas

def get_subscribe_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS[lang]["subscribe_channel_btn"], url="https://t.me/uzinnotech")],
        [InlineKeyboardButton(text=TEXTS[lang]["subscribe_check"], callback_data=f"check_sub_{lang}")]
    ])

def get_language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbek"), KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )

def get_main_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS[lang]["ai_btn"])],
            [KeyboardButton(text=TEXTS[lang]["qr_btn"]), KeyboardButton(text=TEXTS[lang]["pdf_btn"])],
            [KeyboardButton(text=TEXTS[lang]["tts_btn"])]
        ],
        resize_keyboard=True
    )

def get_back_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXTS[lang]["back_btn"])]],
        resize_keyboard=True
    )

def make_qr(data: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()

def make_tts(text: str, lang: str) -> bytes:
    # gTTS "uz" ni qollab-quvvatlamaydi, shuning uchun "tr" ishlatamiz
    lang_map = {"uz": "tr", "ru": "ru", "en": "en"}
    tts_lang = lang_map.get(lang, "tr")
    tts = gTTS(text=text, lang=tts_lang)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()

async def upload_to_fileio(file_bytes: bytes, filename: str):
    # file.io ishlamasa, 0x0.st ga urinib korilamiz
    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field("file", file_bytes, filename=filename)
            form.add_field("expires", "1d")
            async with session.post("https://file.io", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        data = await resp.json()
                        if data.get("success"):
                            return data.get("link")
    except Exception as e:
        logging.error(f"file.io xatosi: {e}")
    # Backup: 0x0.st
    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field("file", file_bytes, filename=filename)
            async with session.post("https://0x0.st", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    link = (await resp.text()).strip()
                    if link.startswith("http"):
                        return link
    except Exception as e:
        logging.error(f"0x0.st xatosi: {e}")
    return None

async def check_and_notify_subscription(message: Message, state: FSMContext) -> bool:
    data = await state.get_data()
    lang = data.get("language", "uz")
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(TEXTS[lang]["unsubscribed_msg"], reply_markup=get_subscribe_keyboard(lang))
        return True
    return False

# ✅ FIX #8: Uzun xabarni bo'lib yuborish helper funksiyasi
async def send_long_message(message: Message, text: str):
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i+4000])
    else:
        await message.answer(text)

@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user = message.from_user
    user_data = {
        "name": user.full_name,
        "username": f"@{user.username}" if user.username else "—",
        "lang": "—",
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    users_db[str(user.id)] = user_data  # ✅ str key JSON uchun
    save_users_db(users_db)             # ✅ Darhol saqlanadi
    await state.set_state(UserState.choosing_language)
    await message.answer(
        "👋 Assalomu aleykum! / Здравствуйте! / Hello!\n\n🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=get_language_keyboard()
    )

@dp.message(Command("stats"))
async def stats_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    total = len(users_db)
    if total == 0:
        await message.answer("📊 Hali hech kim botdan foydalanmagan.")
        return
    langs = {"uz": 0, "ru": 0, "en": 0, "—": 0}
    for u in users_db.values():
        l = u.get("lang", "—")
        langs[l] = langs.get(l, 0) + 1
    last_users = list(users_db.items())[-10:]
    last_text = ""
    for uid, u in reversed(last_users):
        last_text += f"\n👤 {u['name']} {u['username']} | {u['lang']} | {u['date']}"
    text = (
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n\n"
        f"🌐 Tillar:\n"
        f"  🇺🇿 O'zbek: {langs.get('uz', 0)}\n"
        f"  🇷🇺 Rus: {langs.get('ru', 0)}\n"
        f"  🇬🇧 Ingliz: {langs.get('en', 0)}\n\n"
        f"🕐 Oxirgi 10 ta foydalanuvchi:{last_text}"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(UserState.choosing_language)
async def language_selected(message: Message, state: FSMContext):
    text = message.text or ""
    if "🇺🇿" in text:
        lang = "uz"
    elif "🇷🇺" in text:
        lang = "ru"
    elif "🇬🇧" in text:
        lang = "en"
    else:
        await message.answer("Iltimos, tilni tanlang:", reply_markup=get_language_keyboard())
        return
    await state.update_data(language=lang)
    uid = str(message.from_user.id)
    if uid in users_db:
        users_db[uid]["lang"] = lang
        save_users_db(users_db)  # ✅ Til yangilanishi saqlanadi
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(TEXTS[lang]["subscribe_msg"], reply_markup=get_subscribe_keyboard(lang))
        return
    await state.set_state(UserState.main_menu)
    await message.answer(TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

@dp.callback_query(F.data.startswith("check_sub_"))
async def check_sub_callback(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[-1]
    is_subscribed = await check_subscription(callback.from_user.id)
    if is_subscribed:
        await state.update_data(language=lang)
        await state.set_state(UserState.main_menu)
        await callback.message.answer(TEXTS[lang]["subscribe_success"], reply_markup=get_main_keyboard(lang))
        await callback.answer("✅")
    else:
        await callback.answer(TEXTS[lang]["subscribe_error"], show_alert=True)

# ✅ FIX #7: Back handler faqat tegishli holatlarda ishlaydi
@dp.message(F.text.in_(["🔙 Orqaga", "🔙 Назад", "🔙 Back"]))
async def go_back(message: Message, state: FSMContext):
    current_state = await state.get_state()
    # Agar til tanlash holatida bo'lsa, orqaga borishni e'tiborsiz qoldiramiz
    if current_state == UserState.choosing_language:
        return
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.update_data(chat_history=[])
    await state.set_state(UserState.main_menu)
    await message.answer(TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

@dp.message(F.text == "🤖 AI Assistant")
async def ai_start(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.ai_chat)
    await message.answer(TEXTS[lang]["ai_welcome"], reply_markup=get_back_keyboard(lang))

@dp.message(F.text.in_(["📷 QR Kod yaratuvchi", "📷 QR Код генератор", "📷 QR Code Creator"]))
async def qr_start(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.qr_waiting)
    await message.answer(TEXTS[lang]["qr_prompt"], reply_markup=get_back_keyboard(lang))

# ✅ FIX #2: PDF handler barcha 3 tildagi tugmani qamrab oladi
@dp.message(F.text.in_(["📄 PDF Generator", "📄 PDF Генератор"]))
async def pdf_start(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.pdf_waiting)
    await message.answer(TEXTS[lang]["pdf_prompt"], reply_markup=get_back_keyboard(lang))

@dp.message(F.text.in_(["🎙 Matnni ovozga aylantirish", "🎙 Текст в голос", "🎙 Text to Speech"]))
async def tts_start(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.tts_waiting)
    await message.answer(TEXTS[lang]["tts_prompt"], reply_markup=get_back_keyboard(lang))

@dp.message(UserState.main_menu)
async def main_menu_handler(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    text = message.text or ""
    if not text:
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    wait_msg = await message.answer(TEXTS[lang]["thinking"])
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": TEXTS[lang]["bot_system"]},
                {"role": "user", "content": text}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    d = await response.json()
                    reply = d["choices"][0]["message"]["content"]
                else:
                    reply = TEXTS[lang]["qr_error"]
    except Exception as e:
        logging.error(f"Groq xatosi: {e}")
        reply = TEXTS[lang]["qr_error"]
    try:
        await wait_msg.delete()
    except:
        pass
    # ✅ FIX #8: main_menu_handler da ham uzun xabar bo'lib yuboriladi
    await send_long_message(message, reply)

@dp.message(UserState.ai_chat)
async def ai_chat_handler(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    text = message.text or ""
    if not text:
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    if lang == "uz":
        system_msg = "Sen yordamchi AI assistantsan. O'zbek tilida aniq va tushunarli javob ber."
    elif lang == "ru":
        system_msg = "Ты AI-помощник. Отвечай на русском языке четко и понятно."
    else:
        system_msg = "You are a helpful AI assistant. Answer clearly and concisely in English."
    chat_history = data.get("chat_history", [])
    chat_history.append({"role": "user", "content": text})
    if len(chat_history) > 20:
        chat_history = chat_history[-20:]
    wait_msg = await message.answer(TEXTS[lang]["thinking"])
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_msg}, *chat_history],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    d = await response.json()
                    reply = d["choices"][0]["message"]["content"]
                else:
                    reply = TEXTS[lang]["qr_error"]
    except Exception as e:
        logging.error(f"Groq xatosi: {e}")
        reply = TEXTS[lang]["qr_error"]
    chat_history.append({"role": "assistant", "content": reply})
    await state.update_data(chat_history=chat_history)
    try:
        await wait_msg.delete()
    except:
        pass
    await send_long_message(message, reply)

@dp.message(UserState.qr_waiting, F.text)
async def qr_from_text(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    text = message.text or ""
    if text.startswith("/"):
        return
    try:
        qr_bytes = make_qr(text)
        photo = BufferedInputFile(qr_bytes, filename="qrcode.png")
        await message.answer_photo(photo, caption=f"{TEXTS[lang]['qr_success']}\n📝 {text[:100]}{'...' if len(text) > 100 else ''}")
        await message.answer(TEXTS[lang]["qr_prompt"])
    except Exception as e:
        logging.error(f"QR xatosi: {e}")
        await message.answer(TEXTS[lang]["qr_error"])

@dp.message(UserState.qr_waiting, F.photo)
async def qr_from_photo(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    msgs = {
        "uz": "⚠️ QR kod faqat matn va linklar uchun ishlaydi.\nIltimos, matn yoki link yuboring!",
        "ru": "⚠️ QR код работает только для текста и ссылок.\nПожалуйста, отправьте текст или ссылку!",
        "en": "⚠️ QR code only works for text and links.\nPlease send text or a link!"
    }
    await message.answer(msgs.get(lang, msgs["uz"]))

@dp.message(UserState.qr_waiting, F.audio | F.voice | F.document)
async def qr_from_file(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    msgs = {
        "uz": "⚠️ QR kod faqat matn va linklar uchun ishlaydi.\nIltimos, matn yoki link yuboring!",
        "ru": "⚠️ QR код работает только для текста и ссылок.\nПожалуйста, отправьте текст или ссылку!",
        "en": "⚠️ QR code only works for text and links.\nPlease send text or a link!"
    }
    await message.answer(msgs.get(lang, msgs["uz"]))

@dp.message(UserState.pdf_waiting, F.text)
async def generate_pdf(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    text = message.text or ""
    if text.startswith("/"):
        return
    if not text:
        await message.answer(TEXTS[lang]["pdf_prompt"])
        return
    wait_msg = await message.answer(TEXTS[lang]["pdf_processing"])
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(20, 20, 20)

        # ✅ Unicode fontlarni qidirish (bir nechta yo'l)
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
        font_loaded = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdf.add_font("UniFont", "", font_path, uni=True)
                pdf.set_font("UniFont", size=12)
                font_loaded = True
                break

        if not font_loaded:
            # ✅ Unicode font yo'q bo'lsa, harflarni ASCII ga o'girish
            import unicodedata
            def to_ascii(s):
                return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
            text = to_ascii(text)
            pdf.set_font("Helvetica", size=12)

        pdf.set_font_size(16)
        pdf.cell(0, 10, "Document", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font_size(12)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)
        for line in text.split("\n"):
            pdf.multi_cell(0, 8, line if line else " ")
        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        await wait_msg.delete()
        doc = BufferedInputFile(buf.read(), filename="document.pdf")
        await message.answer_document(doc, caption=TEXTS[lang]["pdf_success"])
        await message.answer(TEXTS[lang]["pdf_prompt"])
    except Exception as e:
        logging.error(f"PDF xatosi: {e}")
        try:
            await wait_msg.delete()
        except:
            pass
        await message.answer(TEXTS[lang]["pdf_error"])

# ✅ FIX #4: asyncio.get_event_loop() o'rniga asyncio.get_running_loop()
@dp.message(UserState.tts_waiting, F.text)
async def generate_tts(message: Message, state: FSMContext):
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    text = message.text or ""
    if text.startswith("/"):
        return
    if not text:
        await message.answer(TEXTS[lang]["tts_prompt"])
        return
    wait_msg = await message.answer(TEXTS[lang]["tts_processing"])
    try:
        audio_bytes = await asyncio.get_running_loop().run_in_executor(None, make_tts, text, lang)
        audio_file = BufferedInputFile(audio_bytes, filename="voice.mp3")
        await wait_msg.delete()
        await message.answer_audio(audio_file, caption=TEXTS[lang]["tts_success"])
        await message.answer(TEXTS[lang]["tts_prompt"])
    except Exception as e:
        logging.error(f"TTS xatosi: {e}")
        try:
            await wait_msg.delete()
        except:
            pass
        await message.answer(TEXTS[lang]["tts_error"])

async def main():
    print("🤖 AI Javobchi bot ishga tushdi!")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
