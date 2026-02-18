import logging
import asyncio
import aiohttp
import os
import qrcode
import io
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# === KALITLAR ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === BOT VA DISPATCHER ===
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# === STATE ===
class UserState(StatesGroup):
    choosing_language = State()
    main_menu = State()
    qr_waiting = State()

# === MATNLAR ===
TEXTS = {
    "uz": {
        "language_selected": "✅ Til tanlandi: O'zbek\n\n🤖 Men AI yordamchiman!\nIstalgan savol yozing, javob beraman.",
        "thinking": "🤔 O'ylamoqda...",
        "back": "🔙 Ortga",
        "menu_btn": "📋 Menyu",
        "qr_btn": "📷 QR Kod yaratish",
        "qr_prompt": "📝 QR kodga aylantirilishi kerak bo'lgan matn yoki link yuboring:",
        "qr_success": "✅ QR kod tayyor!",
        "qr_error": "❌ QR kod yaratishda xatolik.",
        "back_main": "🏠 Asosiy menu",
    },
    "ru": {
        "language_selected": "✅ Язык выбран: Русский\n\n🤖 Я AI помощник!\nЗадайте любой вопрос, я отвечу.",
        "thinking": "🤔 Думаю...",
        "back": "🔙 Назад",
        "menu_btn": "📋 Меню",
        "qr_btn": "📷 Создать QR код",
        "qr_prompt": "📝 Отправьте текст или ссылку для QR кода:",
        "qr_success": "✅ QR код готов!",
        "qr_error": "❌ Ошибка при создании QR кода.",
        "back_main": "🏠 Главное меню",
    },
    "en": {
        "language_selected": "✅ Language: English\n\n🤖 I'm an AI assistant!\nAsk me anything.",
        "thinking": "🤔 Thinking...",
        "back": "🔙 Back",
        "menu_btn": "📋 Menu",
        "qr_btn": "📷 Create QR Code",
        "qr_prompt": "📝 Send text or link to generate QR code:",
        "qr_success": "✅ QR code ready!",
        "qr_error": "❌ Error creating QR code.",
        "back_main": "🏠 Main menu",
    }
}

# === KLAVIATURALAR ===
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
            [KeyboardButton(text=TEXTS[lang]["menu_btn"])]
        ],
        resize_keyboard=True
    )

def get_menu_inline(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS[lang]["qr_btn"], callback_data="qr_code")],
    ])

def get_back_inline(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS[lang]["back_main"], callback_data="back_main")]
    ])

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
    text = message.text
    if "🇺🇿" in text:
        lang = "uz"
    elif "🇷🇺" in text:
        lang = "ru"
    elif "🇬🇧" in text:
        lang = "en"
    else:
        await message.answer("Iltimos, tilni tanlang / Пожалуйста, выберите язык / Please choose a language:")
        return
    await state.update_data(language=lang)
    await state.set_state(UserState.main_menu)
    await message.answer(
        TEXTS[lang]["language_selected"],
        reply_markup=get_main_keyboard(lang)
    )

# === MENYU TUGMASI ===
@dp.message(F.text.in_(["📋 Menyu", "📋 Меню", "📋 Menu"]))
async def show_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await message.answer("📋", reply_markup=get_menu_inline(lang))

# === QR KOD CALLBACK ===
@dp.callback_query(F.data == "qr_code")
async def qr_code_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.qr_waiting)
    await callback.message.answer(
        TEXTS[lang]["qr_prompt"],
        reply_markup=get_back_inline(lang)
    )
    await callback.answer()

# === ORTGA CALLBACK ===
@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(UserState.main_menu)
    await callback.message.answer(
        TEXTS[lang]["language_selected"],
        reply_markup=get_main_keyboard(lang)
    )
    await callback.answer()

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
            caption=f"{TEXTS[lang]['qr_success']}\n📝 {text[:50]}{'...' if len(text) > 50 else ''}",
            reply_markup=get_back_inline(lang)
        )
    except Exception as e:
        logging.error(f"QR xatosi: {e}")
        await message.answer(TEXTS[lang]["qr_error"])

    await state.set_state(UserState.main_menu)

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

# === ASOSIY HANDLER ===
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

# === ISHGA TUSHIRISH ===
async def main():
    print("🤖 AI Javobchi bot ishga tushdi!")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
