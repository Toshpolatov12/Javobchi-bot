import logging
import asyncio
import aiohttp
import os
import urllib.parse
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def get_ai_response(text: str) -> str:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": text}]}]}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logging.error(f"Gemini xatosi: {e}")
        return "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring."

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
async def start_handler(message: Message):
    user = message.from_user
    name = user.first_name or user.username or "Do'stim"
    await message.answer(
        f"👋 Salom, *{name}*! Men *AI Javobchi* botman!\n\n"
        "🤖 *Nima qila olaman:*\n"
        "• Har qanday savolingizga javob beraman\n"
        "• Rasm yaratib beraman\n\n"
        "📝 *Qanday ishlatish:*\n"
        "• Shunchaid savol yozing — AI javob beradi\n"
        "• *Rasm:* so'zidan keyin tavsif yozing\n"
        "  _Masalan:_ `Rasm: tog'lar va ko'k osmon`\n\n"
        "❓ Boshlang!",
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🆘 *Yordam*\n\n"
        "• Savol yozing → AI javob beradi\n"
        "• `Rasm: [tavsif]` → Rasm yaratiladi",
        parse_mode="Markdown"
    )

@dp.message()
async def message_handler(message: Message):
    text = message.text or ""
    if not text:
        return

    if text.lower().startswith("rasm:"):
        prompt = text.split(":", 1)[1].strip()
        if not prompt:
            await message.answer("📝 Rasm tavsifini yozing!")
            return
        wait_msg = await message.answer("🎨 Rasm yaratilmoqda... ⏳")
        image_data = await generate_image(prompt)
        await wait_msg.delete()
        if image_data:
            photo = BufferedInputFile(image_data, filename="image.jpg")
            await message.answer_photo(photo, caption=f"🎨 *{prompt}*", parse_mode="Markdown")
        else:
            await message.answer("❌ Rasm yaratishda xatolik.")
    else:
        wait_msg = await message.answer("🤔 O'ylamoqda...")
        response = await get_ai_response(text)
        await wait_msg.delete()
        await message.answer(response)

async def main():
    print("🤖 AI Javobchi bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
