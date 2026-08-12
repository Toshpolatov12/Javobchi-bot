import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
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
