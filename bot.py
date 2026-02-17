import logging
import asyncio
import aiohttp
import os
import urllib.parse
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# === .env fayldan kalitlarni yuklash ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === GEMINI SOZLASH ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# === BOT VA DISPATCHER ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === /start KOMANDASI ===
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Salom! Men *AI Javobchi* botman!\n\n"
        "🤖 *Nima qila olaman:*\n"
        "• Har qanday savolingizga javob beraman\n"
        "• Rasm yaratib beraman\n\n"
        "📝 *Qanday ishlatish:*\n"
        "• Shunchaid savol yozing — AI javob beradi\n"
        "• *Rasm:* so'zidan keyin tavsif yozing — rasm yaratiladi\n"
        "  _Masalan:_ `Rasm: tog'lar va ko'k osmon`\n\n"
        "❓ Boshlang!",
        parse_mode="Markdown"
    )

# === /help KOMANDASI ===
@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🆘 *Yordam*\n\n"
        "• Savol yozing → AI javob beradi\n"
        "• `Rasm: [tavsif]` → Rasm yaratiladi\n\n"
        "_Masalan:_\n"
        "`Rasm: chiroyli gul bog'i`\n"
        "`Python nima?`",
        parse_mode="Markdown"
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

# === AI JAVOB ===
async def get_ai_response(text: str) -> str:
    try:
        response = model.generate_content(text)
        return response.text
    except Exception as e:
        logging.error(f"Gemini xatosi: {e}")
        return "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring."

# === ASOSIY XABAR HANDLER ===
@dp.message()
async def message_handler(message: Message):
    text = message.text or ""
    
    rasm_keywords = ["rasm:", "rasm :", "Rasm:", "RASM:", "image:", "Image:"]
    is_image_request = any(text.lower().startswith(kw.lower()) for kw in rasm_keywords)
    
    if is_image_request:
        prompt = text.split(":", 1)[1].strip() if ":" in text else text
        
        if not prompt:
            await message.answer("📝 Rasm tavsifini yozing!\n_Masalan:_ `Rasm: tog'lar va ko'k osmon`", parse_mode="Markdown")
            return
        
        wait_msg = await message.answer("🎨 Rasm yaratilmoqda... Biroz kuting ⏳")
        image_data = await generate_image(prompt)
        await wait_msg.delete()
        
        if image_data:
            from aiogram.types import BufferedInputFile
            photo = BufferedInputFile(image_data, filename="image.jpg")
            await message.answer_photo(photo, caption=f"🎨 *{prompt}*", parse_mode="Markdown")
        else:
            await message.answer("❌ Rasm yaratishda xatolik. Qayta urinib ko'ring.")
    else:
        if not text:
            return
        wait_msg = await message.answer("🤔 O'ylamoqda...")
        response = await get_ai_response(text)
        await wait_msg.delete()
        
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
