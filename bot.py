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

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

class UserState(StatesGroup):
    choosing_language = State()
    main_menu = State()
    qr_waiting = State()
    pdf_waiting = State()

TEXTS = {
    "uz": {
        "welcome": "✅ Til tanlandi: O'zbek\n\n🤖 Men AI yordamchiman!\nIstalgan savol yozing, javob beraman.",
        "thinking": "🤔 O'ylamoqda...",
        "qr_btn": "📷 QR Kod yaratish",
        "pdf_btn": "📄 PDF Generator",
        "qr_prompt": "📝 QR kodga aylantirilishi kerak bo'lgan matn yoki link yuboring:\n\n(Orqaga qaytish uchun /start bosing)",
        "qr_success": "✅ QR kod tayyor!",
        "qr_error": "❌ QR kod yaratishda xatolik.",
        "pdf_prompt": "📄 Matningizni yuboring, men uni PDF ko'rinishiga keltirib sizga yuboraman!\n\n💡 Quyidagilarni yuborishingiz mumkin:\n• Istalgan matn\n• Maqola yoki hujjat\n• Ro'yxat yoki jadval\n\n(Orqaga qaytish uchun /start bosing)",
        "pdf_success": "✅ PDF tayyor!",
        "pdf_error": "❌ PDF yaratishda xatolik.",
        "pdf_processing": "⏳ PDF yaratilmoqda...",
    },
    "ru": {
        "welcome": "✅ Язык выбран: Русский\n\n🤖 Я AI помощник!\nЗадайте любой вопрос, я отвечу.",
        "thinking": "🤔 Думаю...",
        "qr_btn": "📷 Создать QR код",
        "pdf_btn": "📄 PDF Генератор",
        "qr_prompt": "📝 Отправьте текст или ссылку для QR кода:\n\n(Для возврата нажмите /start)",
        "qr_success": "✅ QR код готов!",
        "qr_error": "❌ Ошибка при создании QR кода.",
        "pdf_prompt": "📄 Отправьте текст, и я преобразую его в PDF!\n\n💡 Вы можете отправить:\n• Любой текст\n• Статью или документ\n• Список или таблицу\n\n(Для возврата нажмите /start)",
        "pdf_success": "✅ PDF готов!",
        "pdf_error": "❌ Ошибка при создании PDF.",
        "pdf_processing": "⏳ Создаю PDF...",
    },
    "en": {
        "welcome": "✅ Language: English\n\n🤖 I'm an AI assistant!\nAsk me anything.",
        "thinking": "🤔 Thinking...",
        "qr_btn": "📷 Create QR Code",
        "pdf_btn": "📄 PDF Generator",
        "qr_prompt": "📝 Send text or link to generate QR code:\n\n(Press /start to go back)",
        "qr_success": "✅ QR code ready!",
        "qr_error": "❌ Error creating QR code.",
        "pdf_prompt": "📄 Send me your text and I'll convert it to PDF!\n\n💡 You can send:\n• Any text\n• Article or document\n• List or table\n\n(Press /start to go back)",
        "pdf_success": "✅ PDF ready!",
        "pdf_error": "❌ Error creating PDF.",
        "pdf_processing": "⏳ Creating PDF...",
    }
}

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
            [KeyboardButton(text=TEXTS[lang]["qr_btn"]), KeyboardButton(text=TEXTS[lang]["pdf_btn"])]
        ],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.set_state(UserState.choosing_language)
    await message.answer(
        "👋 Assalomu aleykum! / Здравствуйте! / Hello!\n\n🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=get_language_keyboard()
    )

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
    await state.set_state(UserState.main_menu)
    await message.answer(TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

# === QR KOD TUGMASI ===
@dp.message(UserState.main_menu, F.text.in_(["📷 QR Kod yaratish", "📷 Создать QR код", "📷 Create QR Code"]))
async def qr_start(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.qr_waiting)
    await message.answer(TEXTS[lang]["qr_prompt"])

# === PDF TUGMASI ===
@dp.message(UserState.main_menu, F.text.in_(["📄 PDF Generator", "📄 PDF Генератор", "📄 PDF Generator"]))
async def pdf_start(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.pdf_waiting)
    await message.answer(TEXTS[lang]["pdf_prompt"])

# === QR KOD YARATISH ===
@dp.message(UserState.qr_waiting)
async def generate_qr(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    text = message.text or ""

    if not text:
        await message.answer(TEXTS[lang]["qr_prompt"])
        return

    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        photo = BufferedInputFile(buf.read(), filename="qrcode.png")
        await message.answer_photo(
            photo,
            caption=f"{TEXTS[lang]['qr_success']}\n📝 {text[:100]}{'...' if len(text) > 100 else ''}"
        )
        await message.answer(TEXTS[lang]["qr_prompt"])
    except Exception as e:
        logging.error(f"QR xatosi: {e}")
        await message.answer(TEXTS[lang]["qr_error"])

# === PDF YARATISH ===
@dp.message(UserState.pdf_waiting)
async def generate_pdf(message: Message, state: FSMContext):
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

        # Unicode shrift
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if os.path.exists(font_path):
            pdf.add_font("DejaVu", "", font_path, uni=True)
            pdf.set_font("DejaVu", size=12)
        else:
            pdf.set_font("Helvetica", size=12)

        # Sarlavha
        pdf.set_font_size(16)
        pdf.cell(0, 10, "Document", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font_size(12)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)

        # Matn
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

# === AI JAVOB ===
async def get_ai_response(text: str, lang: str) -> str:
    try:
        if lang == "uz":
            system_msg = "Sen yordamchi AI assistantsan. O'zbek tilida aniq va tushunarli javob ber."
        elif lang == "ru":
            system_msg = "Ты AI-помощник. Отвечай на русском языке четко и понятно."
        else:
            system_msg = "You are a helpful AI assistant. Answer clearly and concisely in English."

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": text}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Groq error: {response.status}")
    except Exception as e:
        logging.error(f"Groq xatosi: {e}")
        if lang == "uz":
            return "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        elif lang == "ru":
            return "❌ Произошла ошибка. Пожалуйста, попробуйте снова."
        else:
            return "❌ An error occurred. Please try again."

@dp.message(UserState.main_menu)
async def message_handler(message: Message, state: FSMContext):
    text = message.text or ""
    if not text:
        return

    data = await state.get_data()
    lang = data.get("language", "uz")

    wait_msg = await message.answer(TEXTS[lang]["thinking"])
    response = await get_ai_response(text, lang)
    try:
        await wait_msg.delete()
    except:
        pass

    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await message.answer(response[i:i+4000])
    else:
        await message.answer(response)

async def main():
    print("🤖 AI Javobchi bot ishga tushdi!")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
