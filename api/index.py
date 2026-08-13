import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from bot.main import get_bot_instance, get_all_bots, bot, dp
from handlers import start, converter, ai_chat, games, font_handler
from games.snake_html import SNAKE_HTML
from games.game2048_html import GAME2048_HTML

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logger = logging.getLogger(__name__)

# Register routers — ORDER MATTERS!
dp.include_router(start.router)
dp.include_router(converter.router)
dp.include_router(games.router)
dp.include_router(font_handler.router)
dp.include_router(ai_chat.router)

app = FastAPI()


@app.post("/api/webhook/{token}")
@app.post("/api/webhook")
async def webhook(request: Request, token: str = None):
    try:
        data = await request.json()
        target_bot = get_bot_instance(token) if token else bot
        await dp.feed_raw_update(target_bot, data)
    except Exception as e:
        token_sub = token[:10] if token else "default"
        logger.error(f"Webhook error for bot token {token_sub}...: {e}")
    return {"ok": True}


@app.get("/api/webhook")
async def health():
    active_count = len(get_all_bots())
    return {
        "status": "running",
        "bot": "File Converter & Game Multi-Bot Server",
        "active_bots_count": active_count
    }


@app.get("/")
async def root():
    active_count = len(get_all_bots())
    return {
        "status": "running",
        "bot": "File Converter & Game Multi-Bot Server",
        "active_bots_count": active_count
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
