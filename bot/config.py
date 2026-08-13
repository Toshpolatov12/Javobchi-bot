import os

# Multi-bot token support: comma-separated BOT_TOKENS or fallback BOT_TOKEN
BOT_TOKENS_RAW = os.environ.get("BOT_TOKENS", os.environ.get("BOT_TOKEN", ""))
BOT_TOKENS = [t.strip() for t in BOT_TOKENS_RAW.split(",") if t.strip()]
BOT_TOKEN = BOT_TOKENS[0] if BOT_TOKENS else ""

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
CHANNEL = os.environ.get("CHANNEL", "")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB Telegram limit
TEMP_DIR = "/tmp"

# Game configuration
SNAKE_GAME_SHORT_NAME = os.environ.get("SNAKE_GAME_SHORT_NAME", "snake_game")
GAME2048_SHORT_NAME = os.environ.get("GAME2048_SHORT_NAME", "game2048")
APP_URL = os.environ.get("APP_URL", "https://javobchi-bot.vercel.app")


def get_all_bot_tokens() -> list[str]:
    return BOT_TOKENS if BOT_TOKENS else ([BOT_TOKEN] if BOT_TOKEN else [])
