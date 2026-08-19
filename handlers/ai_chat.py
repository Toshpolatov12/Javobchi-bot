import os
import time
import logging
import hashlib
import aiohttp
from aiogram import Router, F
from aiogram.filters import Command
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
from utils.chat_memory import get_user_history, add_chat_turn, clear_user_history

logger = logging.getLogger(__name__)
router = Router()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq modellar ro'yxati (Aug 2026)
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "qwen-qwq-32b",
    "groq/compound",
    "groq/compound-mini",
    "llama-3.3-70b-versatile",
]

# Fast in-memory cache for inline queries to prevent 429 rate limit spamming: query_hash -> (timestamp, response_text)
_INLINE_CACHE: dict[str, tuple[float, str]] = {}
INLINE_CACHE_TTL = 180  # 3 minutes cache


def _get_cached_inline(query_text: str) -> str | None:
    h = hashlib.md5(query_text.strip().lower().encode()).hexdigest()
    entry = _INLINE_CACHE.get(h)
    if entry:
        ts, resp = entry
        if time.time() - ts < INLINE_CACHE_TTL:
            return resp
        _INLINE_CACHE.pop(h, None)
    return None


def _set_cached_inline(query_text: str, response: str):
    h = hashlib.md5(query_text.strip().lower().encode()).hexdigest()
    _INLINE_CACHE[h] = (time.time(), response)
    # Prune old cache if size exceeds 300
    if len(_INLINE_CACHE) > 300:
        now = time.time()
        for k in list(_INLINE_CACHE.keys())[:100]:
            if now - _INLINE_CACHE[k][0] > INLINE_CACHE_TTL:
                _INLINE_CACHE.pop(k, None)


async def get_groq_response(messages: list[dict] | str, model_index: int = 0) -> str:
    key = groq_rotator.get_key()
    if not key:
        return "⚠️ Groq API key sozlanmagan."

    if model_index >= len(GROQ_MODELS):
        return "❌ Hech qanday AI model ishlamayapti. Keyinroq urinib ko'ring."

    model = GROQ_MODELS[model_index]

    if isinstance(messages, str):
        msg_list = [{"role": "user", "content": messages}]
    else:
        msg_list = messages

    system_prompt = {
        "role": "system",
        "content": (
            "Siz aqlli, xushmuomala va foydali AI yordamchisiz. "
            "Foydalanuvchi bilan samimiy suhbatlashing. Suhbat tarixidagi avvalgi savol-javoblarni "
            "doimo inobatga olgan holda mantiqiy va kontekstga mos javob bering."
        )
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [system_prompt] + msg_list,
        "temperature": 0.7,
        "max_tokens": 1500
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                elif resp.status == 404:
                    logger.warning(f"Groq model '{model}' not found (404). Trying next model...")
                    return await get_groq_response(messages, model_index + 1)
                elif resp.status in (429, 403):
                    logger.warning(f"Groq 429/quota error on model '{model}'. Rotating...")
                    groq_rotator.mark_busy()
                    # Try next key if available
                    next_key = groq_rotator.get_key()
                    if next_key and next_key != key:
                        return await get_groq_response(messages, model_index)
                    # If same key, try alternative model (e.g. gpt-oss-20b or compound-mini)
                    if model_index + 1 < len(GROQ_MODELS):
                        return await get_groq_response(messages, model_index + 1)
                    return "❌ AI xizmati vaqtincha band (429 Rate limit)."
                else:
                    error_text = await resp.text()
                    logger.error(f"Groq API error {resp.status} with model '{model}': {error_text[:200]}")
                    if model_index + 1 < len(GROQ_MODELS):
                        return await get_groq_response(messages, model_index + 1)
                    return "❌ AI xizmati vaqtincha ishlamayapti."
    except aiohttp.ClientTimeout:
        return "⏰ Javob vaqti tugadi. Qayta urinib ko'ring."
    except Exception as e:
        logger.error(f"Groq request error: {e}")
        return "❌ Xatolik yuz berdi."


async def get_gemini_response(messages: list[dict] | str) -> str:
    key = gemini_rotator.get_key()
    if not key:
        return "⚠️ Gemini API key sozlanmagan."

    url = f"{GEMINI_URL}?key={key}"

    if isinstance(messages, str):
        contents = [{"role": "user", "parts": [{"text": messages}]}]
    else:
        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 1500,
            "temperature": 0.7
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                elif resp.status in (429, 403):
                    logger.warning(f"Gemini 429/quota error on key: {key[:8]}... Rotating key...")
                    gemini_rotator.mark_busy()
                    next_key = gemini_rotator.get_key()
                    if next_key and next_key != key:
                        return await get_gemini_response(messages)
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


async def get_ai_response(messages: list[dict] | str) -> str:
    """Gets AI response with automatic fallback across Groq and Gemini."""
    if not groq_rotator.is_empty():
        resp = await get_groq_response(messages)
        # If Groq fails with rate limit or error, fallback to Gemini
        if (resp.startswith("❌") or resp.startswith("⚠️")) and not gemini_rotator.is_empty():
            logger.info("Groq unavailable, falling back to Gemini...")
            gemini_resp = await get_gemini_response(messages)
            if not gemini_resp.startswith("❌") and not gemini_resp.startswith("⚠️"):
                return gemini_resp
        return resp
    elif not gemini_rotator.is_empty():
        return await get_gemini_response(messages)
    else:
        return "⚠️ AI API key sozlanmagan."


@router.message(Command("clear", "newchat", "reset", "tozala"))
async def clear_chat_command(message: Message):
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    await clear_user_history(user_id)
    clear_msg = {
        "uz": "🧹 <b>Suhbat xotirasi tozalandi!</b>\n\nYangi mavzuda savol berishingiz mumkin.",
        "ru": "🧹 <b>История диалога очищена!</b>\n\nМожете начать новую тему.",
        "en": "🧹 <b>Conversation history cleared!</b>\n\nYou can start a new topic."
    }.get(lang, "🧹 <b>Suhbat xotirasi tozalandi!</b>")
    await message.answer(clear_msg, parse_mode="HTML")


@router.message(F.text.in_([
    "🤖 AI rejim", "🤖 AI режим", "🤖 AI Mode",
    "🤖 AI Suhbat", "🤖 AI Чат"
]))
async def ai_mode_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    ai_text = MESSAGES[lang]["ai_mode"] + (
        "\n\n💡 <i>Mavzuni tozalab yangidan boshlash uchun /clear buyrug'ini yuboring.</i>"
        if lang == "uz" else
        "\n\n💡 <i>Чтобы очистить контекст и начать заново, отправьте /clear.</i>"
        if lang == "ru" else
        "\n\n💡 <i>Send /clear to reset context and start fresh.</i>"
    )
    await message.answer(ai_text, parse_mode="HTML")


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
    bot_token_id = message.bot.token[:10] if message.bot and message.bot.token else "bot"
    url = extract_url(message.text)

    if url:
        # 1. Video URL handling
        if is_video_url(url):
            try:
                await message.bot.send_chat_action(message.chat.id, "upload_video")
            except Exception:
                pass
            thinking_msg = await message.answer(MESSAGES[lang]["downloading_video"])
            video_path = await download_video(url)

            if video_path and os.path.exists(video_path):
                try:
                    video_file = FSInputFile(video_path)
                    await message.answer_video(video_file, caption="✅ Video yuklab olindi!")
                    await thinking_msg.delete()
                    await log_activity(user_id, "video_download", url, "success", bot_username=bot_token_id)
                except Exception as e:
                    logger.error(f"Error sending downloaded video: {e}")
                    await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
                    await log_activity(user_id, "video_download", url, f"error: {str(e)[:50]}", bot_username=bot_token_id)
                finally:
                    cleanup(video_path)
            else:
                await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
                await log_activity(user_id, "video_download", url, "failed", bot_username=bot_token_id)
            return

        # 2. General webpage article URL handling
        try:
            await message.bot.send_chat_action(message.chat.id, "typing")
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
            await log_activity(user_id, "web_summary", url, "success", bot_username=bot_token_id)
        else:
            await thinking_msg.edit_text(MESSAGES[lang]["video_error"])
            await log_activity(user_id, "web_summary", url, "failed", bot_username=bot_token_id)
        return

    # 3. Standard Multi-Turn Conversational AI Chat
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
    except Exception:
        pass

    thinking_msg = await message.answer(MESSAGES[lang].get("ai_thinking", "⏳..."))

    # Load recent conversation history
    history = await get_user_history(user_id)
    current_messages = history + [{"role": "user", "content": message.text}]

    # Query AI with complete dialog context
    response = await get_ai_response(current_messages)
    await log_activity(user_id, "ai_query", message.text[:100], "success", bot_username=bot_token_id)

    # Save to history if valid response
    if response and not response.startswith("❌") and not response.startswith("⚠️"):
        await add_chat_turn(user_id, message.text, response)

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
    bot_token_id = query.bot.token[:10] if query.bot and query.bot.token else "bot"

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
        await query.answer(games, cache_time=300, is_personal=True)
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
            await query.answer(results, cache_time=300, is_personal=True)
            await log_activity(user_id, "inline_video_query", url, "success", bot_username=bot_token_id)
            return

    # 3. QUERY IS TEXT -> Return AI answer article
    # Check fast cache first to avoid firing API on every single keystroke
    cached_resp = _get_cached_inline(query_text)
    if cached_resp:
        response = cached_resp
    else:
        response = await get_ai_response(query_text)
        if response and not response.startswith("❌") and not response.startswith("⚠️"):
            _set_cached_inline(query_text, response)

    await log_activity(user_id, "inline_ai_query", query_text[:100], "success", bot_username=bot_token_id)

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
    # Set cache_time=60 so Telegram client caches response for 60s instead of re-querying every keystroke
    await query.answer(results, cache_time=60, is_personal=True)
