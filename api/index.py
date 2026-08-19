import logging
import aiohttp
from fastapi import FastAPI, Request
from bot.main import get_bot_by_id, get_bot_instance, get_all_bots, BOT_ID_TO_TOKEN, BOT_INSTANCES, dp
from bot.config import get_all_bot_tokens, APP_URL, GROQ_API_KEY, GEMINI_API_KEY
from handlers import start, converter, ai_chat, font_handler, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Register routers — ORDER MATTERS!
dp.include_router(admin.router)
dp.include_router(start.router)
dp.include_router(converter.router)
dp.include_router(font_handler.router)
dp.include_router(ai_chat.router)

app = FastAPI()


@app.post("/api/webhook/{bot_id}")
@app.post("/api/webhook")
async def webhook(request: Request, bot_id: str = None):
    """
    Handles incoming Telegram webhook updates for multi-bot and single-bot modes.
    URL: /api/webhook/896218801 or fallback /api/webhook
    """
    try:
        data = await request.json()
        target_bot = get_bot_by_id(bot_id)
        if not target_bot:
            logger.error(f"No bot found for bot_id: {bot_id}")
            return {"ok": False, "error": f"unknown bot_id: {bot_id}"}
        await dp.feed_raw_update(target_bot, data)
    except Exception as e:
        logger.error(f"Webhook error for bot_id {bot_id}: {e}")
    return {"ok": True}


@app.get("/api/webhook/{bot_id}")
@app.get("/api/webhook")
@app.get("/api/ping")
@app.get("/ping")
async def health(bot_id: str = None):
    """Health check / auto-ping endpoint to prevent server sleep."""
    return {
        "status": "running",
        "bot": "File Converter & AI Multi-Bot Server",
        "active_bots": list(BOT_ID_TO_TOKEN.keys())
    }


@app.get("/api/setup-webhooks")
async def setup_webhooks():
    """
    Barcha botlar uchun webhook'larni avtomatik o'rnatish.
    Brauzerda: https://javobchi-bot.vercel.app/api/setup-webhooks
    """
    results = []
    base_url = APP_URL.rstrip("/")

    for token in get_all_bot_tokens():
        bot_id = token.split(":")[0]
        webhook_url = f"{base_url}/api/webhook/{bot_id}"
        telegram_api = f"https://api.telegram.org/bot{token}/setWebhook"

        try:
            async with aiohttp.ClientSession() as session:
                # Set webhook
                async with session.post(
                    telegram_api,
                    json={"url": webhook_url},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    set_result = await resp.json()

                # Get bot info
                async with session.get(
                    f"https://api.telegram.org/bot{token}/getMe",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as info_resp:
                    info = await info_resp.json()
                    bot_username = info.get("result", {}).get("username", "unknown")

                results.append({
                    "bot": f"@{bot_username}",
                    "bot_id": bot_id,
                    "webhook_url": webhook_url,
                    "telegram_response": set_result
                })
                logger.info(f"Webhook set for @{bot_username} (ID:{bot_id}): {set_result}")

        except Exception as e:
            results.append({
                "bot_id": bot_id,
                "error": str(e)
            })
            logger.error(f"Failed to set webhook for bot_id {bot_id}: {e}")

    return {
        "status": "completed",
        "bots_configured": len(results),
        "results": results
    }


@app.get("/")
async def root():
    return {
        "status": "running",
        "bot": "File Converter & AI Multi-Bot Server",
        "active_bots": list(BOT_ID_TO_TOKEN.keys()),
        "setup": "Visit /api/setup-webhooks to auto-register all bot webhooks"
    }


@app.get("/api/test-ai")
async def test_ai():
    """AI API kalitlarini test qilish — brauzerda oching va xato sababini ko'ring."""
    from utils.token_rotator import groq_rotator, gemini_rotator

    results = {
        "env_vars": {
            "GROQ_API_KEY_set": bool(GROQ_API_KEY),
            "GROQ_API_KEY_prefix": GROQ_API_KEY[:12] + "..." if GROQ_API_KEY else "NOT SET",
            "GEMINI_API_KEY_set": bool(GEMINI_API_KEY),
            "GEMINI_API_KEY_prefix": GEMINI_API_KEY[:12] + "..." if GEMINI_API_KEY else "NOT SET",
        },
        "rotators": {
            "groq_keys_count": len(groq_rotator.keys),
            "groq_keys_prefixes": [k[:12] + "..." for k in groq_rotator.keys] if groq_rotator.keys else [],
            "gemini_keys_count": len(gemini_rotator.keys),
            "gemini_keys_prefixes": [k[:12] + "..." for k in gemini_rotator.keys] if gemini_rotator.keys else [],
        },
        "groq_test": None,
        "gemini_test": None
    }

    # Test Groq — try multiple models to find one that works
    if groq_rotator.keys:
        key = groq_rotator.get_key()
        groq_models = [
            "openai/gpt-oss-120b", "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b", "qwen-qwq-32b",
            "groq/compound", "groq/compound-mini",
            "llama-3.3-70b-versatile"
        ]
        model_results = []
        for model in groq_models:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": "Say hi"}],
                            "max_tokens": 5
                        },
                        headers={
                            "Authorization": f"Bearer {key}",
                            "Content-Type": "application/json"
                        },
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        body = await resp.text()
                        model_results.append({
                            "model": model,
                            "status_code": resp.status,
                            "works": resp.status == 200,
                            "response": body[:200]
                        })
                        if resp.status == 200:
                            break  # Found a working model, stop testing
            except Exception as e:
                model_results.append({"model": model, "error": str(e)})
        results["groq_test"] = model_results

    # Test Gemini
    if gemini_rotator.keys:
        key = gemini_rotator.get_key()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
                    json={"contents": [{"parts": [{"text": "Say hi"}]}]},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    body = await resp.text()
                    results["gemini_test"] = {
                        "status_code": resp.status,
                        "response": body[:500]
                    }
        except Exception as e:
            results["gemini_test"] = {"error": str(e)}

    return results
