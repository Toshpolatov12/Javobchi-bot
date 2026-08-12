import os
import logging
import hashlib
import aiohttp
from aiogram import Router, F
from aiogram.types import (
    Message, InlineQuery, InlineQueryResultArticle, InlineQueryResultVideo,
    InlineQueryResultGame, InputTextMessageContent, FSInputFile
)
from bot.config import (
    SNAKE_GAME_SHORT_NAME, GAME2048_SHORT_NAME
)
from bot.database import get_user_lang, log_activity
from bot.locales import MESSAGES
from utils.link_downloader import (
    extract_url, is_video_url, extract_video_info,
    download_video, scrape_webpage
)
from utils.file_helper import cleanup
from utils.token_rotator import groq_rotator, gemini_rotator
from bot.main import bot

logger = logging.getLogger(__name__)
router = Router()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


async def get_groq_response(prompt: str) -> str:
    key = groq_rotator.get_key()
    if not key:
        return "⚠️ Groq API key sozlanmagan."

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
                elif resp.status in (429, 403):
                    logger.warning(f"Groq 429/quota error on key: {key[:8]}... Rotating key...")
                    groq_rotator.mark_busy()
                    next_key = groq_rotator.get_key()
                    if next_key and next_key != key:
                        return await get_groq_response(prompt)
                    return "❌ AI xizmati vaqtincha band (429 Rate limit)."
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
    key = gemini_rotator.get_key()
    if not key:
        return "⚠️ Gemini API key sozlanmagan."

    url = f"{GEMINI_URL}?key={key}"
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
                elif resp.status in (429, 403):
                    logger.warning(f"Gemini 429/quota error on key: {key[:8]}... Rotating key...")
                    gemini_rotator.mark_busy()
                    next_key = gemini_rotator.get_key()
                    if next_key and next_key != key:
                        return await get_gemini_response(prompt)
                    return "❌ AI xizmati vaqtincha band (429 Rate limit)."
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
    if not groq_rotator.is_empty():
        return await get_groq_response(prompt)
    elif not gemini_rotator.is_empty():
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
    user_id = message.from_user.id
    url = extract_url(message.text)

    if url:
        # 1. Video URL handling
        if is_video_url(url):
            try:
                await bot.send_chat_action(message.chat.id, "upload_video")
            except Exception:
                pass
            thinking_msg = await message.answer(MESSAGES[lang]["downloading_video"])
            video_path = await download_video(url)

            if video_path and os.path.exists(video_path):
                try:
                    video_file = FSInputFile(video_path)
                    await message.answer_video(video_file, caption="✅ Video yuklab olindi!")
                    await thinking_msg.delete()
                    await log_activity(user_id, "video_download", url, "success")
                except Exception as e:
                    logger.error(f"Error sending downloaded video: {e}")
                    await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
                    await log_activity(user_id, "video_download", url, f"error: {str(e)[:50]}")
                finally:
                    cleanup(video_path)
            else:
                await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
                await log_activity(user_id, "video_download", url, "failed")
            return

        # 2. General webpage article URL handling
        try:
            await bot.send_chat_action(message.chat.id, "typing")
        except Exception:
            pass
        thinking_msg = await message.answer(MESSAGES[lang]["scraping_web"])
        web_text = await scrape_webpage(url)

        if web_text:
            prompt = (
                f"Quyidagi veb-sahifa matnini qisqa va loqin tarzda foydalanuvchi tilida ({lang}) umumlashtirib ber:\n\n"
                f"{web_text}"
            )
            summary = await get_ai_response(prompt)
            await thinking_msg.edit_text(f"🌐 <b>Veb-sahifa mazmuni:</b>\n\n{summary}", parse_mode="HTML")
            await log_activity(user_id, "web_summary", url, "success")
        else:
            await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
            await log_activity(user_id, "web_summary", url, "failed")
        return

    # 3. Standard AI Chat (no URL)
    try:
        await bot.send_chat_action(message.chat.id, "typing")
    except Exception:
        pass

    thinking_msg = await message.answer(MESSAGES[lang].get("ai_thinking", "⏳..."))
    response = await get_ai_response(message.text)
    await log_activity(user_id, "ai_query", message.text[:100], "success")

    if len(response) > 4000:
        response = response[:4000] + "\n\n... (qisqartirildi)"

    try:
        await thinking_msg.edit_text(response)
    except Exception:
        await thinking_msg.edit_text(response[:4000])


@router.inline_query()
async def inline_ai(query: InlineQuery):
    query_text = (query.query or "").strip()
    user_id = query.from_user.id

    # 1. EMPTY QUERY -> Return Games (Snake and 2048)
    if not query_text:
        games = [
            InlineQueryResultGame(
                id="game_snake",
                game_short_name=SNAKE_GAME_SHORT_NAME
            ),
            InlineQueryResultGame(
                id="game_2048",
                game_short_name=GAME2048_SHORT_NAME
            )
        ]
        await query.answer(games, cache_time=300)
        return

    if len(query_text) < 3:
        return

    url = extract_url(query_text)
    result_id = hashlib.md5(query_text.encode()).hexdigest()

    # 2. QUERY CONTAINS VIDEO URL -> Return playable inline video!
    if url and is_video_url(url):
        info = await extract_video_info(url)
        if info and info.get("url"):
            direct_url = info["url"]
            title = info.get("title", "Video")
            thumb = info.get("thumbnail", "https://png.pngtree.com/png-vector/20190215/ourmid/pngtree-play-video-icon-png-image_533038.jpg")

            results = [
                InlineQueryResultVideo(
                    id=result_id,
                    video_url=direct_url,
                    mime_type="video/mp4",
                    thumbnail_url=thumb,
                    title=f"🎬 {title[:40]}",
                    caption=f"🎬 <b>{title}</b>\n\n🔗 {url}",
                    parse_mode="HTML"
                )
            ]
            await query.answer(results, cache_time=300)
            await log_activity(user_id, "inline_video_query", url, "success")
            return

    # 3. QUERY IS TEXT -> Return AI answer article
    response = await get_ai_response(query_text)
    await log_activity(user_id, "inline_ai_query", query_text[:100], "success")

    if len(response) > 4000:
        response = response[:4000] + "..."

    results = [
        InlineQueryResultArticle(
            id=result_id,
            title="🤖 AI Javob",
            description=response[:100],
            input_message_content=InputTextMessageContent(
                message_text=f"❓ <b>{query_text}</b>\n\n🤖 {response}",
                parse_mode="HTML"
            )
        )
    ]
    await query.answer(results, cache_time=5)
