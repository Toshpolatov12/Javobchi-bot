import logging
import asyncio
import aiohttp
import os
import urllib.parse
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, URLInputFile
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

# === MATNLAR ===
TEXTS = {
    "uz": {
        "language_selected": "✅ Til tanlandi: O'zbek\n\n🤖 Men AI yordamchiman!\n\n📝 Qanday ishlatish:\n• Savol yozing — javob beraman\n• 'Rasm:' dan keyin tavsif yozing — rasm yarataman\n\n💡 Misol:\n• Python nima?\n• Rasm: toglar va kok osmon",
        "thinking": "🤔 O'ylamoqda...",
        "generating_image": "🎨 Rasm yaratilmoqda... Biroz kuting",
        "image_error": "❌ Rasm yaratishda xatolik. Qayta urinib koring.",
        "back": "🔙 Ortga",
    },
    "ru": {
        "language_selected": "✅ Язык выбран: Русский\n\n🤖 Я AI помощник!\n\n📝 Как использовать:\n• Напишите вопрос — отвечу\n• Напишите 'Изображение:' и описание — создам картинку\n\n💡 Пример:\n• Что такое Python?\n• Изображение: горы и голубое небо",
        "thinking": "🤔 Думаю...",
        "generating_image": "🎨 Создаю изображение... Подождите",
        "image_error": "❌ Ошибка при создании изображения. Попробуйте снова.",
        "back": "🔙 Назад",
    },
    "en": {
        "language_selected": "✅ Language selected: English\n\n🤖 I'm an AI assistant!\n\n📝 How to use:\n• Ask a question — I'll answer\n• Type 'Image:' followed by description — I'll generate it\n\n💡 Example:\n• What is Python?\n• Image: mountains and blue sky",
        "thinking": "🤔 Thinking...",
        "generating_image": "🎨 Generating image... Please wait",
        "image_error": "❌ Error generating image. Please try again.",
        "back": "🔙 Back",
    }
}

# === KLAVIATURA ===
def get_language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbek"), KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )

def get_back_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXTS[lang]["back"])]],
        resize_keyboard=True
    )

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
    await message.answer(TEXTS[lang]["language_selected"], reply_markup=get_back_keyboard(lang))

# === ORTGA ===
@dp.message(F.text.in_(["🔙 Ortga", "🔙 Назад", "🔙 Back"]))
async def back_to_language(message: Message, state: FSMContext):
    await state.set_state(UserState.choosing_language)
    await message.answer(
        "🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=get_language_keyboard()
    )

# === TARJIMA ===
async def translate_to_english(prompt: str, lang: str) -> str:
    if lang == "en":
        return prompt
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "Translate the following text to English for image generation. Return ONLY the translated text, nothing else."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Tarjima xatosi: {e}")
    return prompt

# === RASM URL YARATISH ===
def generate_image_url(prompt: str) -> str:
    encoded = urllib.parse.quote(prompt)
    seed = abs(hash(prompt)) % 99999
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"

# === GROQ AI ===
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
    data = await state.get_data()
    lang = data.get("language", "uz")

    image_keywords = {
        "uz": ["rasm:"],
        "ru": ["изображение:", "картинка:"],
        "en": ["image:", "picture:"]
    }

    is_image_request = any(text.lower().startswith(kw) for kw in image_keywords[lang])

    if is_image_request:
        prompt = text.split(":", 1)[1].strip() if ":" in text else ""
        if not prompt:
            await message.answer("📝 Rasm tavsifini yozing!" if lang == "uz" else "📝 Напишите описание!" if lang == "ru" else "📝 Write description!")
            return

        wait_msg = await message.answer(TEXTS[lang]["generating_image"])

        # Tarjima
        prompt_en = await translate_to_english(prompt, lang)
        logging.info(f"Prompt: '{prompt}' -> '{prompt_en}'")

        # URL yaratish
        image_url = generate_image_url(prompt_en)
        logging.info(f"Rasm URL: {image_url}")

        try:
            await wait_msg.delete()
        except:
            pass

        try:
            photo = URLInputFile(image_url, filename="image.png", timeout=60)
            await message.answer_photo(photo, caption=f"🎨 {prompt}")
        except Exception as e:
            logging.error(f"Rasm yuborishda xato: {e}")
            # Fallback: URL ni matn sifatida yuborish
            await message.answer(f"🎨 {prompt}\n\n{image_url}")

    else:
        if not text:
            return
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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
