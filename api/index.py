import logging
from fastapi import FastAPI, Request
from bot.main import bot, dp
from aiogram.types import Update
from handlers import start, converter, ai_chat

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Register routers — ORDER MATTERS!
# start.py handles commands and menu buttons
# converter.py handles files and photos
# ai_chat.py handles ALL remaining text (must be LAST)
dp.include_router(start.router)
dp.include_router(converter.router)
dp.include_router(ai_chat.router)

app = FastAPI()


@app.post("/api/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"ok": True}


@app.get("/api/webhook")
async def health():
    return {"status": "running", "bot": "File Converter Bot"}


@app.get("/")
async def root():
    return {"status": "running", "bot": "File Converter Bot"}
