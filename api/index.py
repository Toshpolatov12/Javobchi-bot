import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from bot.main import bot, dp
from handlers import start, converter, ai_chat, games
from games.snake_html import SNAKE_HTML
from games.game2048_html import GAME2048_HTML

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Register routers — ORDER MATTERS!
dp.include_router(start.router)
dp.include_router(converter.router)
dp.include_router(games.router)
dp.include_router(ai_chat.router)

app = FastAPI()


@app.post("/api/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        await dp.feed_raw_update(bot, data)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"ok": True}


@app.get("/api/webhook")
async def health():
    return {"status": "running", "bot": "File Converter & Game Bot"}


@app.get("/")
async def root():
    return {"status": "running", "bot": "File Converter & Game Bot"}


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
