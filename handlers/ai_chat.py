import os
import logging
import hashlib
import aiohttp
from aiogram import Router, F
from aiogram.types import (
    Message, InlineQuery, InlineQueryResultArticle,
    InputTextMessageContent, FSInputFile
)
from bot.config import GEMINI_API_KEY, GROQ_API_KEY
from bot.database import get_user_lang
from bot.locales import MESSAGES
from utils.link_downloader import extract_url, is_video_url, download_video, scrape_webpage
from utils.file_helper import cleanup

logger = logging.getLogger(__name__)
router = Router()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


async def get_groq_response(prompt: str, key: str) -> str:
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Siz foydali AI yordamchisiz. Foydalanuvchiga aniq, ravon va xushmuomala javob bering."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await resp.text()
                    logger.error(f"Groq API error {resp.status}: {error_text[:200]}")
                    return "❌ AI xizmati vaqtincha ishlamayapti."
    except aiohttp.ClientTimeout:
        return "⏰ Javob vaqti tugadi. Qayta urinib ko'ring."
    except Exception as e:
        logger.error(f"Groq request error: {e}")
        return "❌ Xatolik yuz berdi."


async def get_gemini_response(prompt: str) -> str:
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature": 0.7
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    error_text = await resp.text()
                    logger.error(f"Gemini API error {resp.status}: {error_text[:200]}")
                    return "❌ AI xizmati vaqtincha ishlamayapti."
    except aiohttp.ClientTimeout:
        return "⏰ Javob vaqti tugadi. Qayta urinib ko'ring."
    except Exception as e:
        logger.error(f"Gemini request error: {e}")
        return "❌ Xatolik yuz berdi."


async def get_ai_response(prompt: str) -> str:
    if GROQ_API_KEY:
        return await get_groq_response(prompt, GROQ_API_KEY)
    elif GEMINI_API_KEY and GEMINI_API_KEY.startswith("gsk_"):
        return await get_groq_response(prompt, GEMINI_API_KEY)
    elif GEMINI_API_KEY:
        return await get_gemini_response(prompt)
    else:
        return "⚠️ AI API key sozlanmagan."


@router.message(F.text.in_([
    "🤖 AI rejim", "🤖 AI режим", "🤖 AI Mode",
    "🤖 AI Suhbat", "🤖 AI Чат"
]))
async def ai_mode_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(MESSAGES[lang]["ai_mode"], parse_mode="HTML")


@router.message(F.text & ~F.text.startswith("/"))
async def chat_handler(message: Message):
    menu_texts = [
        "📁 Fayl transfer", "📁 Конвертация файлов", "📁 File Transfer",
        "📁 Konvertatsiya", "📁 Конвертация",
        "🌐 Til / Language", "🌐 Til", "🌐 Язык", "🌐 Language",
        "❓ Yordam", "❓ Помощь", "❓ Help",
        "🤖 AI rejim", "🤖 AI режим", "🤖 AI Mode",
        "🤖 AI Suhbat", "🤖 AI Чат",
        "⬅️ Orqaga", "⬅️ Назад", "⬅️ Back"
    ]
    if message.text in menu_texts:
        return

    lang = await get_user_lang(message.from_user.id)
    url = extract_url(message.text)

    if url:
        # 1. Video URL handling
        if is_video_url(url):
            thinking_msg = await message.answer(MESSAGES[lang]["downloading_video"])
            video_path = await download_video(url)

            if video_path and os.path.exists(video_path):
                try:
                    video_file = FSInputFile(video_path)
                    await message.answer_video(video_file, caption="✅ Video yuklab olindi!")
                    await thinking_msg.delete()
                except Exception as e:
                    logger.error(f"Error sending downloaded video: {e}")
                    await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
                finally:
                    cleanup(video_path)
            else:
                # Video download failed (too large, private, or unavailable)
                await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
            return

        # 2. General webpage article URL handling
        thinking_msg = await message.answer(MESSAGES[lang]["scraping_web"])
        web_text = await scrape_webpage(url)

        if web_text:
            prompt = (
                f"Quyidagi veb-sahifa matnini qisqa va loqin tarzda foydalanuvchi tilida ({lang}) umumlashtirib ber:\n\n"
                f"{web_text}"
            )
            summary = await get_ai_response(prompt)
            await thinking_msg.edit_text(f"🌐 <b>Veb-sahifa mazmuni:</b>\n\n{summary}", parse_mode="HTML")
        else:
            await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
        return

    # 3. Standard AI Chat (no URL)
    thinking_msg = await message.answer(MESSAGES[lang].get("ai_thinking", "⏳..."))
    response = await get_ai_response(message.text)

    if len(response) > 4000:
        response = response[:4000] + "\n\n... (qisqartirildi)"

    try:
        await thinking_msg.edit_text(response)
    except Exception:
        await thinking_msg.edit_text(response[:4000])


@router.inline_query()
async def inline_ai(query: InlineQuery):
    if not query.query or len(query.query) < 3:
        return

    response = await get_ai_response(query.query)
    result_id = hashlib.md5(query.query.encode()).hexdigest()

    if len(response) > 4000:
        response = response[:4000] + "..."

    results = [
        InlineQueryResultArticle(
            id=result_id,
            title="🤖 AI Javob",
            description=response[:100],
            input_message_content=InputTextMessageContent(
                message_text=f"❓ <b>{query.query}</b>\n\n🤖 {response}",
                parse_mode="HTML"
            )
        )
    ]
    await query.answer(results, cache_time=5)
