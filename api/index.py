import logging
import aiohttp
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from bot.main import get_bot_instance, get_all_bots, BOT_INSTANCES, dp
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

# --- Token-to-Bot lookup for fast webhook routing ---
_TOKEN_BOT_MAP = {}


def _build_token_map():
    """Build a mapping of token -> Bot instance for all configured tokens."""
    _TOKEN_BOT_MAP.clear()
    for token in get_all_bot_tokens():
        try:
            bot_instance = get_bot_instance(token)
            _TOKEN_BOT_MAP[token] = bot_instance
            logger.info(f"Registered bot for token: {token[:15]}...")
        except Exception as e:
            logger.error(f"Failed to register bot for token {token[:15]}...: {e}")


_build_token_map()


@app.post("/api/webhook/{token:path}")
async def webhook(request: Request, token: str):
    """Each bot gets its own webhook URL: /api/webhook/BOT_TOKEN"""
    try:
        data = await request.json()
        target_bot = _TOKEN_BOT_MAP.get(token)
        if not target_bot:
            # Try creating on the fly (in case map wasn't built)
            try:
                target_bot = get_bot_instance(token)
                _TOKEN_BOT_MAP[token] = target_bot
            except Exception:
                logger.error(f"Unknown bot token in webhook: {token[:15]}...")
                return {"ok": False, "error": "unknown token"}
        await dp.feed_raw_update(target_bot, data)
    except Exception as e:
        logger.error(f"Webhook error for token {token[:15]}...: {e}")
    return {"ok": True}


@app.get("/api/webhook")
async def health():
    return {
        "status": "running",
        "bot": "File Converter & Game Multi-Bot Server",
        "active_bots_count": len(_TOKEN_BOT_MAP)
    }


@app.get("/api/setup-webhooks")
async def setup_webhooks():
    """
    Barcha botlar uchun webhook'larni avtomatik o'rnatish.
    Brauzerda oching: https://javobchi-bot.vercel.app/api/setup-webhooks
    """
    results = []
    base_url = APP_URL.rstrip("/")

    for token in get_all_bot_tokens():
        webhook_url = f"{base_url}/api/webhook/{token}"
        telegram_api = f"https://api.telegram.org/bot{token}/setWebhook"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    telegram_api,
                    json={"url": webhook_url},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    bot_info_url = f"https://api.telegram.org/bot{token}/getMe"
                    async with session.get(bot_info_url) as info_resp:
                        info = await info_resp.json()
                        bot_username = info.get("result", {}).get("username", "unknown")

                    results.append({
                        "bot": f"@{bot_username}",
                        "token_prefix": f"{token[:15]}...",
                        "webhook_url": f"{base_url}/api/webhook/{token[:15]}...",
                        "telegram_response": data
                    })
                    logger.info(f"Webhook set for @{bot_username}: {data}")
        except Exception as e:
            results.append({
                "token_prefix": f"{token[:15]}...",
                "error": str(e)
            })
            logger.error(f"Failed to set webhook for {token[:15]}...: {e}")

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
        "active_bots_count": len(_TOKEN_BOT_MAP),
        "setup_hint": "Visit /api/setup-webhooks to auto-register all bot webhooks"
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
