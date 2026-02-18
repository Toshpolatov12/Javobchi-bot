import logging
import asyncio
import aiohttp
import os
import urllib.parse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# === KALITLAR ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_API_KEY = os.environ.get("HF_API_KEY")

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
        "language_selected": "✅ Til tanlandi: O'zbek\n\n🤖 Men AI yordamchiman!\n\n📝 Qanday ishlatish:\n• Savol yozing — javob beraman\n• 'Rasm:' dan keyin tavsif yozing — rasm yarataman\n\n💡 Misol:\n• Python nima?\n• Rasm: tog'lar va ko'k osmon",
        "thinking": "🤔 O'ylamoqda...",
        "generating_image": "🎨 Rasm yaratilmoqda... Biroz kuting ⏳",
        "image_error": "❌ Rasm yaratishda xatolik. Qayta urinib ko'ring.",
        "back": "🔙 Ortga",
    },
    "ru": {
        "language_selected": "✅ Язык выбран: Русский\n\n🤖 Я AI помощник!\n\n📝 Как использовать:\n• Напишите вопрос — отвечу\n• Напишите 'Изображение:' и описание — создам картинку\n\n💡 Пример:\n• Что такое Python?\n• Изображение: горы и голубое небо",
        "thinking": "🤔 Думаю...",
        "generating_image": "🎨 Создаю изображение... Подождите ⏳",
        "image_error": "❌ Ошибка при создании изображения. Попробуйте снова.",
        "back": "🔙 Назад",
    },
    "en": {
        "language_selected": "✅ Language selected: English\n\n🤖 I'm an AI assistant!\n\n📝 How to use:\n• Ask a question — I'll answer\n• Type 'Image:' followed by description — I'll generate it\n\n💡 Example:\n• What is Python?\n• Image: mountains and blue sky",
        "thinking": "🤔 Thinking...",
        "generating_image": "🎨 Generating image... Please wait ⏳",
        "image_error": "❌ Error generating image. Please try again.",
        "back": "🔙 Back",
    }
}

# === KLAVIATURA ===
def get_language_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbek"), KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_back_keyboard(lang):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS[lang]["back"])]
        ],
        resize_keyboard=True
    )
    return keyboard

# === /start KOMANDASI ===
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
    
    if "🇺🇿" in text or text == "uz":
        lang = "uz"
    elif "🇷🇺" in text or text == "ru":
        lang = "ru"
    elif "🇬🇧" in text or text == "en":
        lang = "en"
    else:
        await message.answer("Iltimos, tilni tanlang / Пожалуйста, выберите язык / Please choose a language:")
        return
    
    await state.update_data(language=lang)
    await state.set_state(UserState.main_menu)
    
    await message.answer(
        TEXTS[lang]["language_selected"],
        reply_markup=get_back_keyboard(lang)
    )

# === ORTGA QAYTISH ===
@dp.message(F.text.in_(["🔙 Ortga", "🔙 Назад", "🔙 Back"]))
async def back_to_language(message: Message, state: FSMContext):
    await state.set_state(UserState.choosing_language)
    await message.answer(
        "🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=get_language_keyboard()
    )

# === RASM GENERATSIYA ===
async def generate_image(prompt: str) -> bytes | None:
    try:
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": prompt}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    return await response.read()
    except Exception as e:
        logging.error(f"HF xatosi: {e}")
    
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e2:
        logging.error(f"Pollinations xatosi: {e2}")
    return None

# === GROQ AI JAVOB ===
async def get_ai_response(text: str, lang: str) -> str:
    try:
        # Tilga mos system prompt
        if lang == "uz":
            system_msg = "Sen yordamchi AI assistantsan. O'zbek tilida aniq va tushunarli javob ber."
        elif lang == "ru":
            system_msg = "Ты AI-помощник. Отвечай на русском языке четко и понятно."
        else:
            system_msg = "You are a helpful AI assistant. Answer clearly and concisely in English."
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
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
                    error_text = await response.text()
                    logging.error(f"Groq xatosi: {response.status} - {error_text}")
                    raise Exception(f"Groq API error: {response.status}")
    
    except Exception as e:
        logging.error(f"Groq xatosi: {e}")
        if lang == "uz":
            return "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        elif lang == "ru":
            return "❌ Произошла ошибка. Пожалуйста, попробуйте снова."
        else:
            return "❌ An error occurred. Please try again."

# === ASOSIY XABAR HANDLER ===
@dp.message(UserState.main_menu)
async def message_handler(message: Message, state: FSMContext):
    text = message.text or ""
    
    # Til olish
    data = await state.get_data()
    lang = data.get("language", "uz")
    
    # Rasm so'rovi tekshirish
    image_keywords = {
        "uz": ["rasm:", "Rasm:"],
        "ru": ["изображение:", "Изображение:", "картинка:", "Картинка:"],
        "en": ["image:", "Image:", "picture:", "Picture:"]
    }
    
    is_image_request = any(text.lower().startswith(kw.lower()) for kw in image_keywords[lang])
    
    if is_image_request:
        # Rasm yaratish
        prompt = text.split(":", 1)[1].strip() if ":" in text else ""
        
        if not prompt:
            await message.answer(
                "📝 Rasm tavsifini yozing!" if lang == "uz" 
                else "📝 Напишите описание изображения!" if lang == "ru"
                else "📝 Write image description!",
                reply_markup=get_back_keyboard(lang)
            )
            return
        
        wait_msg = await message.answer(TEXTS[lang]["generating_image"])
        image_data = await generate_image(prompt)
        await wait_msg.delete()
        
        if image_data:
            from aiogram.types import BufferedInputFile
            photo = BufferedInputFile(image_data, filename="image.jpg")
            await message.answer_photo(photo, caption=f"🎨 {prompt}")
        else:
            await message.answer(TEXTS[lang]["image_error"])
    
    else:
        # AI javob
        if not text:
            return
        
        wait_msg = await message.answer(TEXTS[lang]["thinking"])
        response = await get_ai_response(text, lang)
        await wait_msg.delete()
        
        # Javob uzun bo'lsa bo'lib yuborish
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await message.answer(chunk)
        else:
            await message.answer(response)

# === BOTNI ISHGA TUSHIRISH ===
async def main():
    print("🤖 AI Javobchi bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
