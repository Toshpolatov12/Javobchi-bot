import logging
import aiohttp
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from bot.main import get_bot_by_id, get_all_bots, BOT_ID_TO_TOKEN, BOT_INSTANCES, dp
from bot.config import get_all_bot_tokens, APP_URL
from handlers import start, converter, ai_chat, games, font_handler
from games.snake_html import SNAKE_HTML
from games.game2048_html import GAME2048_HTML

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Register routers — ORDER MATTERS!
dp.include_router(start.router)
dp.include_router(converter.router)
dp.include_router(games.router)
dp.include_router(font_handler.router)
dp.include_router(ai_chat.router)

app = FastAPI()


@app.post("/api/webhook/{bot_id}")
async def webhook(request: Request, bot_id: str):
    """
    Har bir bot o'z webhook URL'iga ega:
    /api/webhook/896218801  (faqat raqamli bot ID, ':' belgisi yo'q)
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


@app.get("/api/webhook")
async def health():
    return {
        "status": "running",
        "bot": "File Converter & Game Multi-Bot Server",
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
        "bot": "File Converter & Game Multi-Bot Server",
        "active_bots": list(BOT_ID_TO_TOKEN.keys()),
        "setup": "Visit /api/setup-webhooks to auto-register all bot webhooks"
    }


# --- HTML5 Games Hosting Routes ---

@app.get("/games/snake", response_class=HTMLResponse)
async def serve_snake_game():
    return HTMLResponse(content=SNAKE_HTML)


@app.get("/games/2048", response_class=HTMLResponse)
async def serve_2048_game():
    return HTMLResponse(content=GAME2048_HTML)


@app.post("/api/set-score")
async def set_score(request: Request):
    try:
        data = await request.json()
        score = data.get("score", 0)
        game_name = data.get("game", "unknown")
        logger.info(f"New score submitted: {score} for {game_name}")
        return {"status": "success", "score": score}
    except Exception as e:
        logger.error(f"Error handling score submit: {e}")
        return {"status": "error"}
