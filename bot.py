import logging
import asyncio
import aiohttp
import os
import urllib.parse
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("API_key")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

class UserState(StatesGroup):
    language = State()

TEXTS = {
    "uz": {
        "choose_lang": "🌐 Tilni tanlang / Choose language / Выберите язык:",
        "welcome": "👋 Salom, *{name}*! Men *AI Javobchi* botman!\n\n🤖 *Nima qila olaman:*\n• Har qanday savolingizga javob beraman\n• Rasm yaratib beraman\n\n📝 *Qanday ishlatish:*\n• Shunchaki savol yozing — AI javob beradi\n• *Rasm:* so'zidan keyin tavsif yozing\n  _Masalan:_ `Rasm: tog'lar va ko'k osmon`\n\n❓ Boshlang!",
        "help": "🆘 *Yordam*\n\n• Savol yozing → AI javob beradi\n• `Rasm: [tavsif]` → Rasm yaratiladi",
        "thinking": "🤔 O'ylamoqda...",
        "generating": "🎨 Rasm yaratilmoqda... ⏳",
        "error": "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.",
        "image_error": "❌ Rasm yaratishda xatolik.",
        "back": "⬅️ Ortga",
        "lang_changed": "✅ Til o'zgartirildi!"
    },
    "ru": {
        "choose_lang": "🌐 Tilni tanlang / Choose language / Выберите язык:",
        "welcome": "👋 Здравствуйте, *{name}*! Я *AI Помощник* бот!\n\n🤖 *Что я умею:*\n• Отвечаю на любые вопросы\n• Генерирую изображения\n\n📝 *Как использовать:*\n• Просто напишите вопрос — AI ответит\n• Слово *Картинка:* затем описание\n  _Например:_ `Картинка: горы и голубое небо`\n\n❓ Начнем!",
        "help": "🆘 *Помощь*\n\n• Напишите вопрос → AI ответит\n• `Картинка: [описание]` → Создам изображение",
        "thinking": "🤔 Думаю...",
        "generating": "🎨 Генерирую изображение... ⏳",
        "error": "❌ Произошла ошибка. Попробуйте еще раз.",
        "image_error": "❌ Ошибка при создании изображения.",
        "back": "⬅️ Назад",
        "lang_changed": "✅ Язык изменен!"
    },
    "en": {
        "choose_lang": "🌐 Tilni tanlang / Choose language / Выберите язык:",
        "welcome": "👋 Hello, *{name}*! I'm *AI Assistant* bot!\n\n🤖 *What I can do:*\n• Answer any questions\n• Generate images\n\n📝 *How to use:*\n• Just write a question — AI will answer\n• Word *Image:* then description\n  _Example:_ `Image: mountains and blue sky`\n\n❓ Let's start!",
        "help": "🆘 *Help*\n\n• Write a question → AI will answer\n• `Image: [description]` → Generate image",
        "thinking": "🤔 Thinking...",
        "generating": "🎨 Generating image... ⏳",
        "error": "❌ An error occurred. Please try again.",
        "image_error": "❌ Error generating image.",
        "back": "⬅️ Back",
        "lang_changed": "✅ Language changed!"
    }
}

def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    return keyboard

def get_back_keyboard(lang):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS[lang]["back"], callback_data="back_to_lang")]
    ])
    return keyboard

async def get_ai_response(text: str, lang: str) -> str:
    try:
        # Tilga qarab so'rovni tarjima qilish uchun prompt qo'shamiz
        prompt_prefix = {
            "uz": "Javobni o'zbek tilida ber: ",
            "ru": "Ответь на русском языке: ",
            "en": "Answer in English: "
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt_prefix[lang] + text}]}]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
                if "candidates" in data:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                elif "error" in data:
                    logging.error(f"Gemini error: {data['error']}")
                    return TEXTS[lang]["error"]
                else:
                    return TEXTS[lang]["error"]
    except Exception as e:
        logging.error(f"Gemini xatosi: {e}")
        return TEXTS[lang]["error"]

async def generate_image(prompt: str) -> bytes | None:
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        logging.error(f"Rasm xatosi: {e}")
    return None

@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await message.answer(
        TEXTS["uz"]["choose_lang"],
        reply_markup=get_language_keyboard()
    )

@dp.callback_query(F.data.startswith("lang_"))
async def language_callback(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    
    user = callback.from_user
    name = user.first_name or user.username or "Do'stim"
    
    await callback.message.edit_text(
        TEXTS[lang]["welcome"].format(name=name),
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_lang")
async def back_to_language(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        TEXTS["uz"]["choose_lang"],
        reply_markup=get_language_keyboard()
    )
    await callback.answer()

@dp.message(Command("help"))
async def help_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await message.answer(TEXTS[lang]["help"], parse_mode="Markdown")

@dp.message()
async def message_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    
    if not lang:
        await message.answer(
            TEXTS["uz"]["choose_lang"],
            reply_markup=get_language_keyboard()
        )
        return
    
    text = message.text or ""
    if not text:
        return

    # Tilga qarab rasm so'zlarini aniqlash
    image_keywords = {
        "uz": ["rasm:", "rasm :", "Rasm:", "RASM:"],
        "ru": ["картинка:", "Картинка:", "КАРТИНКА:", "картинка :", "Картинка :", "изображение:", "Изображение:"],
        "en": ["image:", "Image:", "IMAGE:", "image :", "Image :", "picture:", "Picture:"]
    }
    
    is_image_request = any(text.lower().startswith(kw.lower()) for kw in image_keywords[lang])
    
    if is_image_request:
        prompt = text.split(":", 1)[1].strip() if ":" in text else text
        if not prompt:
            await message.answer("📝 " + ("Rasm tavsifini yozing!" if lang == "uz" else "Опишите изображение!" if lang == "ru" else "Describe the image!"))
            return
        
        wait_msg = await message.answer(TEXTS[lang]["generating"])
        image_data = await generate_image(prompt)
        await wait_msg.delete()
        
        if image_data:
            photo = BufferedInputFile(image_data, filename="image.jpg")
            await message.answer_photo(photo, caption=f"🎨 *{prompt}*", parse_mode="Markdown")
        else:
            await message.answer(TEXTS[lang]["image_error"])
    else:
        wait_msg = await message.answer(TEXTS[lang]["thinking"])
        response = await get_ai_response(text, lang)
        await wait_msg.delete()
        await message.answer(response)

async def main():
    print("🤖 AI Javobchi bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
