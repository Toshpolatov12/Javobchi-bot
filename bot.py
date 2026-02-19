import logging
import asyncio
import aiohttp
import os
import qrcode
import io
from fpdf import FPDF
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CHANNEL = "@uzinnotech"

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

TEXTS = {
    "uz": {
        "subscribe_msg": (
            "⚠️ Botdan foydalanish uchun kanalga obuna bo'lishingiz kerak!\n\n"
            "👇 Quyidagi tugmani bosib kanalga o'ting va obuna bo'ling:"
        ),
        # ✅ O'ZGARTIRILDI: Har bir til uchun alohida tugma matni
        "subscribe_channel_btn": "📢 Kanalga o'tish",
        "subscribe_check": "✅ Obuna bo'ldim",
        "subscribe_error": "❌ Siz hali obuna bo'lmagansiz!\n\nIltimos, avval kanalga obuna bo'ling 👇",
        "subscribe_success": "✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.",
        # ✅ YANGI: Kanaldan chiqib ketganda ko'rsatiladigan xabar
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
        "back_btn": "🔙 Orqaga",
        "thinking": "🤔 O'ylamoqda...",
        "ai_welcome": "🤖 AI Assistant yoqildi!\nIstalgan savolingizni yozing.\n\n(Orqaga: 🔙 Orqaga)",
        "qr_prompt": "📷 Quyidagilardan birini yuboring:\n• Matn yoki link\n• Rasm 🖼\n• Ovoz/audio 🎵\n\n(Orqaga: 🔙 Orqaga)",
        "qr_uploading": "⏳ Fayl yuklanmoqda...",
        "qr_success": "✅ QR kod tayyor!",
        "qr_file_success": "✅ Fayl yuklandi va QR kod tayyor!\n🔗 Link:",
        "qr_error": "❌ Xatolik yuz berdi.",
        "pdf_prompt": "📄 Matningizni yuboring, PDF ga aylantirib beraman!\n\n(Orqaga: 🔙 Orqaga)",
        "pdf_success": "✅ PDF tayyor!",
        "pdf_error": "❌ PDF yaratishda xatolik.",
        "pdf_processing": "⏳ PDF yaratilmoqda...",
        "bot_system": (
            "Sen AI Javobchi botsан. Bu bot https://t.me/toshpolatov12 tomonidan yaratilgan. "
            "Foydalanuvchi faqat bot haqida savol berishi mumkin. "
            "Bot nima qila olishi: AI bilan suhbat, QR kod yaratish, PDF yaratish. "
            "AI funksiyasi haqida so'ralsa: AI Assistant aqlli suhbat qura oladi, suhbat davomida oxirgi 20 ta xabarni eslab qoladi, "
            "ya'ni oldingi savollar va javoblar asosida muomala qiladi. Orqaga tugmasi bosilganda esa suhbat tarixi tozalanadi va yangi suhbat boshlanadi. "
            "Boshqa savollarga: 'Bosh sahifada faqat bot haqidagi ma'lumotlarni bilib olishingiz mumkin. "
            "AI Assistant tugmasini bosing!' deb javob ber. O'zbek tilida gapir."
        ),
    },
    "ru": {
        "subscribe_msg": (
            "⚠️ Для использования бота нужно подписаться на канал!\n\n"
            "👇 Нажмите кнопку ниже и подпишитесь:"
        ),
        # ✅ O'ZGARTIRILDI
        "subscribe_channel_btn": "📢 Перейти на канал",
        "subscribe_check": "✅ Я подписался",
        "subscribe_error": "❌ Вы ещё не подписались!\n\nПожалуйста, сначала подпишитесь на канал 👇",
        "subscribe_success": "✅ Подписка подтверждена! Можете пользоваться ботом.",
        # ✅ YANGI
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
        "back_btn": "🔙 Назад",
        "thinking": "🤔 Думаю...",
        "ai_welcome": "🤖 AI Assistant включён!\nЗадайте любой вопрос.\n\n(Назад: 🔙 Назад)",
        "qr_prompt": "📷 Отправьте одно из следующего:\n• Текст или ссылку\n• Изображение 🖼\n• Аудио/голос 🎵\n\n(Назад: 🔙 Назад)",
        "qr_uploading": "⏳ Загрузка файла...",
        "qr_success": "✅ QR код готов!",
        "qr_file_success": "✅ Файл загружен, QR готов!\n🔗 Ссылка:",
        "qr_error": "❌ Произошла ошибка.",
        "pdf_prompt": "📄 Отправьте текст, преобразую в PDF!\n\n(Назад: 🔙 Назад)",
        "pdf_success": "✅ PDF готов!",
        "pdf_error": "❌ Ошибка при создании PDF.",
        "pdf_processing": "⏳ Создаю PDF...",
        "bot_system": (
            "Ты бот AI Javobchi, созданный https://t.me/toshpolatov12. "
            "Пользователь может спрашивать только о боте. "
            "Что умеет бот: AI чат, создание QR кода, создание PDF. "
            "Если спросят об AI функции: AI Assistant умеет вести умный диалог, запоминает последние 20 сообщений в разговоре, "
            "то есть отвечает с учётом предыдущих вопросов и ответов. При нажатии кнопки 'Назад' история разговора очищается и начинается заново. "
            "На другие вопросы: 'На главной странице только о боте. Нажмите AI Assistant!' Говори по-русски."
        ),
    },
    "en": {
        "subscribe_msg": (
            "⚠️ You need to subscribe to our channel to use this bot!\n\n"
            "👇 Click the button below to subscribe:"
        ),
        # ✅ O'ZGARTIRILDI
        "subscribe_channel_btn": "📢 Go to Channel",
        "subscribe_check": "✅ I subscribed",
        "subscribe_error": "❌ You haven't subscribed yet!\n\nPlease subscribe to the channel first 👇",
        "subscribe_success": "✅ Subscription confirmed! You can use the bot now.",
        # ✅ YANGI
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
        "back_btn": "🔙 Back",
        "thinking": "🤔 Thinking...",
        "ai_welcome": "🤖 AI Assistant activated!\nAsk me anything.\n\n(Back: 🔙 Back)",
        "qr_prompt": "📷 Send one of the following:\n• Text or link\n• Image 🖼\n• Audio/voice 🎵\n\n(Back: 🔙 Back)",
        "qr_uploading": "⏳ Uploading file...",
        "qr_success": "✅ QR code ready!",
        "qr_file_success": "✅ File uploaded, QR ready!\n🔗 Link:",
        "qr_error": "❌ An error occurred.",
        "pdf_prompt": "📄 Send text and I'll convert it to PDF!\n\n(Back: 🔙 Back)",
        "pdf_success": "✅ PDF ready!",
        "pdf_error": "❌ Error creating PDF.",
        "pdf_processing": "⏳ Creating PDF...",
        "bot_system": (
            "You are AI Javobchi bot, created by https://t.me/toshpolatov12. "
            "User can only ask about the bot. "
            "Bot features: AI chat, QR code, PDF. "
            "If asked about the AI feature: AI Assistant can hold smart conversations and remembers the last 20 messages, "
            "meaning it responds based on previous questions and answers. When the 'Back' button is pressed, the conversation history is cleared and a new chat begins. "
            "For other questions: 'On main page you can only learn about the bot. Press AI Assistant!' Speak English."
        ),
    }
}

# === OBUNA TEKSHIRISH ===
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status not in ["left", "kicked", "banned"]
    except Exception as e:
        logging.error(f"Obuna tekshirish xatosi: {e}")
        return False

# ✅ O'ZGARTIRILDI: Tugma matni tanlangan tilga qarab chiqadi
def get_subscribe_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=TEXTS[lang]["subscribe_channel_btn"],
            url="https://t.me/uzinnotech"
        )],
        [InlineKeyboardButton(
            text=TEXTS[lang]["subscribe_check"],
            callback_data=f"check_sub_{lang}"
        )]
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
            [KeyboardButton(text=TEXTS[lang]["qr_btn"]), KeyboardButton(text=TEXTS[lang]["pdf_btn"])]
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

async def upload_to_fileio(file_bytes: bytes, filename: str):
    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field("file", file_bytes, filename=filename)
            form.add_field("expires", "1d")
            async with session.post("https://file.io", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        return data.get("link")
    except Exception as e:
        logging.error(f"file.io xatosi: {e}")
    return None

# ✅ YANGI YORDAMCHI FUNKSIYA: Har bir xabarda obunani tekshiradi
# Agar obuna bo'lmasa, xabar yuboradi va True qaytaradi (ishni to'xtatish kerak)
async def check_and_notify_subscription(message: Message, state: FSMContext) -> bool:
    data = await state.get_data()
    lang = data.get("language", "uz")
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(
            TEXTS[lang]["unsubscribed_msg"],
            reply_markup=get_subscribe_keyboard(lang)
        )
        return True  # to'xtatish kerak
    return False  # davom etish mumkin

# === /start ===
@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.set_state(UserState.choosing_language)
    await message.answer(
        "👋 Assalomu aleykum! / Здравствуйте! / Hello!\n\n🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=get_language_keyboard()
    )

# === TIL TANLASH ===
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

    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        # ✅ Tugma tanlangan tilda chiqadi
        await message.answer(TEXTS[lang]["subscribe_msg"], reply_markup=get_subscribe_keyboard(lang))
        return

    await state.set_state(UserState.main_menu)
    await message.answer(TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

# === OBUNA TEKSHIRISH CALLBACK ===
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

# === ORQAGA ===
@dp.message(F.text.in_(["🔙 Orqaga", "🔙 Назад", "🔙 Back"]))
async def go_back(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    # ✅ YANGI: AI suhbat tarixini tozalash
    await state.update_data(chat_history=[])
    await state.set_state(UserState.main_menu)
    await message.answer(TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

# === AI TUGMASI ===
@dp.message(F.text == "🤖 AI Assistant")
async def ai_start(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.ai_chat)
    await message.answer(TEXTS[lang]["ai_welcome"], reply_markup=get_back_keyboard(lang))

# === QR TUGMASI ===
@dp.message(F.text.in_(["📷 QR Kod yaratuvchi", "📷 QR Код генератор", "📷 QR Code Creator"]))
async def qr_start(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.qr_waiting)
    await message.answer(TEXTS[lang]["qr_prompt"], reply_markup=get_back_keyboard(lang))

# === PDF TUGMASI ===
@dp.message(F.text.in_(["📄 PDF Generator", "📄 PDF Генератор"]))
async def pdf_start(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.pdf_waiting)
    await message.answer(TEXTS[lang]["pdf_prompt"], reply_markup=get_back_keyboard(lang))

# === BOSH SAHIFA ===
@dp.message(UserState.main_menu)
async def main_menu_handler(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
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
    await message.answer(reply)

# === AI CHAT ===
@dp.message(UserState.ai_chat)
async def ai_chat_handler(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
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

    # ✅ YANGI: Suhbat tarixini olish
    chat_history = data.get("chat_history", [])

    # Foydalanuvchi xabarini tarixga qo'shish
    chat_history.append({"role": "user", "content": text})

    # Tarix juda uzun bo'lib ketmasin — oxirgi 20 ta xabar saqlanadi
    if len(chat_history) > 20:
        chat_history = chat_history[-20:]

    wait_msg = await message.answer(TEXTS[lang]["thinking"])
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_msg},
                *chat_history  # ✅ Butun suhbat tarixi yuboriladi
            ],
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

    # ✅ YANGI: AI javobini ham tarixga qo'shish
    chat_history.append({"role": "assistant", "content": reply})

    # Tarixni saqlash
    await state.update_data(chat_history=chat_history)

    try:
        await wait_msg.delete()
    except:
        pass
    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await message.answer(reply[i:i+4000])
    else:
        await message.answer(reply)

# === QR - MATN ===
@dp.message(UserState.qr_waiting, F.text)
async def qr_from_text(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    text = message.text or ""
    try:
        qr_bytes = make_qr(text)
        photo = BufferedInputFile(qr_bytes, filename="qrcode.png")
        await message.answer_photo(photo, caption=f"{TEXTS[lang]['qr_success']}\n📝 {text[:100]}{'...' if len(text) > 100 else ''}")
        await message.answer(TEXTS[lang]["qr_prompt"])
    except Exception as e:
        logging.error(f"QR xatosi: {e}")
        await message.answer(TEXTS[lang]["qr_error"])

# === QR - RASM ===
@dp.message(UserState.qr_waiting, F.photo)
async def qr_from_photo(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    wait_msg = await message.answer(TEXTS[lang]["qr_uploading"])
    try:
        file = await bot.get_file(message.photo[-1].file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        buf.seek(0)
        link = await upload_to_fileio(buf.read(), "image.jpg")
        await wait_msg.delete()
        if link:
            qr_bytes = make_qr(link)
            photo = BufferedInputFile(qr_bytes, filename="qrcode.png")
            await message.answer_photo(photo, caption=f"{TEXTS[lang]['qr_file_success']}\n{link}")
        else:
            await message.answer(TEXTS[lang]["qr_error"])
        await message.answer(TEXTS[lang]["qr_prompt"])
    except Exception as e:
        logging.error(f"Rasm QR xatosi: {e}")
        try: await wait_msg.delete()
        except: pass
        await message.answer(TEXTS[lang]["qr_error"])

# === QR - AUDIO/FAYL ===
@dp.message(UserState.qr_waiting, F.audio | F.voice | F.document)
async def qr_from_file(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    wait_msg = await message.answer(TEXTS[lang]["qr_uploading"])
    try:
        if message.audio:
            file_id = message.audio.file_id
            filename = message.audio.file_name or "audio.mp3"
        elif message.voice:
            file_id = message.voice.file_id
            filename = "voice.ogg"
        else:
            file_id = message.document.file_id
            filename = message.document.file_name or "file"
        file = await bot.get_file(file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        buf.seek(0)
        link = await upload_to_fileio(buf.read(), filename)
        await wait_msg.delete()
        if link:
            qr_bytes = make_qr(link)
            photo = BufferedInputFile(qr_bytes, filename="qrcode.png")
            await message.answer_photo(photo, caption=f"{TEXTS[lang]['qr_file_success']}\n{link}")
        else:
            await message.answer(TEXTS[lang]["qr_error"])
        await message.answer(TEXTS[lang]["qr_prompt"])
    except Exception as e:
        logging.error(f"Fayl QR xatosi: {e}")
        try: await wait_msg.delete()
        except: pass
        await message.answer(TEXTS[lang]["qr_error"])

# === PDF ===
@dp.message(UserState.pdf_waiting, F.text)
async def generate_pdf(message: Message, state: FSMContext):
    # ✅ Obunani tekshir
    if await check_and_notify_subscription(message, state):
        return
    data = await state.get_data()
    lang = data.get("language", "uz")
    text = message.text or ""
    if not text:
        await message.answer(TEXTS[lang]["pdf_prompt"])
        return
    wait_msg = await message.answer(TEXTS[lang]["pdf_processing"])
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(20, 20, 20)
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if os.path.exists(font_path):
            pdf.add_font("DejaVu", "", font_path, uni=True)
            pdf.set_font("DejaVu", size=12)
        else:
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
        try: await wait_msg.delete()
        except: pass
        await message.answer(TEXTS[lang]["pdf_error"])

async def main():
    print("🤖 AI Javobchi bot ishga tushdi!")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
