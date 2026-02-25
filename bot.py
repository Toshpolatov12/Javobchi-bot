import logging
import json
import asyncio
import aiohttp
import base64
import os
import io
import csv
import codecs
import unicodedata
from datetime import datetime

import qrcode
from gtts import gTTS
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN      = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ADMIN_ID       = int(os.environ.get("ADMIN_ID", "7189342638"))
CHANNEL        = "@uzinnotech"
DB_FILE        = "users_db.json"
WEATHER_KEY    = os.environ.get("WEATHER_API_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def db_load():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def db_save(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"DB save error: {e}")

users_db = db_load()
storage  = MemoryStorage()
bot      = Bot(token=BOT_TOKEN)
dp       = Dispatcher(storage=storage)

class S(StatesGroup):
    lang      = State()
    menu      = State()
    ai_chat   = State()
    qr        = State()
    pdf       = State()
    tts       = State()
    excel     = State()
    wm_photo  = State()
    wm_text   = State()
    weather   = State()

T = {
    "uz": {
        "sub_msg":      "\u26a0\ufe0f Botdan foydalanish uchun kanalga obuna bo'ling!\n\n\U0001f447 Quyidagi tugmani bosing:",
        "sub_btn":      "\U0001f4e2 Kanalga o'tish",
        "sub_check":    "\u2705 Obuna bo'ldim",
        "sub_error":    "\u274c Siz hali obuna bo'lmagansiz! Iltimos, avval kanalga obuna bo'ling \U0001f447",
        "sub_ok":       "\u2705 Obuna tasdiqlandi! Xush kelibsiz!",
        "unsub_msg":    "\u26a0\ufe0f Siz kanaldan chiqib ketgansiz!\n\nDavom etish uchun qayta obuna bo'ling \U0001f447",
        "welcome":      "\U0001f44b Salom, <b>{name}</b>!\n\n\U0001f916 Men <b>AI Javobchi</b> \u2014 aqlli ko'p funksiyali botman.\n\n\U0001f4cc Quyidagi bo'limlardan birini tanlang:",
        "ai_btn":       "\U0001f916 AI Suhbat",
        "qr_btn":       "\U0001f4f7 QR Kod",
        "pdf_btn":      "\U0001f4c4 PDF",
        "tts_btn":      "\U0001f399 Matndan Ovoz",
        "excel_btn":    "\U0001f4ca Excel",
        "wm_btn":       "\U0001f5bc Rasmga Matn",
        "back_btn":     "\U0001f519 Orqaga",
        "ai_welcome":   "\U0001f916 <b>AI Suhbat</b> rejimi!\n\n\U0001f4ac Matn, rasm yoki ovoz xabar yuboring.\n\U0001f4cc Orqaga: <b>\U0001f519 Orqaga</b>",
        "ai_thinking":  "\u23f3 Fikrlamoqda...",
        "ai_error":     "\u274c Xatolik yuz berdi. Qayta urinib ko'ring.",
        "qr_welcome":   "\U0001f4f7 <b>QR Kod</b> generatori!\n\n\u270f\ufe0f Matn yoki link yuboring.\n\U0001f4cc Orqaga: <b>\U0001f519 Orqaga</b>",
        "qr_success":   "\u2705 QR kod tayyor!",
        "qr_error":     "\u274c QR yaratishda xatolik.",
        "qr_only_text": "\u26a0\ufe0f Faqat <b>matn yoki link</b> yuboring.",
        "pdf_welcome":  "\U0001f4c4 <b>PDF Generator</b>!\n\n\u270f\ufe0f Matn yuboring. Bir nechta qism yuborishingiz mumkin.\n\U0001f4cc Orqaga: <b>\U0001f519 Orqaga</b>",
        "pdf_collect":  "\U0001f4dd Qabul qilindi! <b>{parts}</b> qism, <b>{chars}</b> belgi.\n\nDavom etasizmi?",
        "pdf_done_btn": "\u2705 PDF yaratish",
        "pdf_undo_btn": "\u21a9\ufe0f Oxirgini o'chirish",
        "pdf_cleared":  "\u21a9\ufe0f Oxirgi qism o'chirildi.",
        "pdf_empty":    "\u26a0\ufe0f Matn yo'q. Avval biror narsa yuboring.",
        "pdf_process":  "\u23f3 PDF yaratilmoqda...",
        "pdf_success":  "\u2705 PDF tayyor!",
        "pdf_error":    "\u274c PDF yaratishda xatolik.",
        "tts_welcome":  "\U0001f399 <b>Matndan Ovoz</b>!\n\n\u270f\ufe0f Matn yuboring.\n\U0001f4cc Orqaga: <b>\U0001f519 Orqaga</b>",
        "tts_process":  "\u23f3 Ovoz yaratilmoqda...",
        "tts_success":  "\u2705 Ovoz tayyor!",
        "tts_error":    "\u274c Ovoz yaratishda xatolik.",
        "excel_welcome":"\U0001f4ca <b>Excel Generator</b>!\n\nFormat:\n<code>Ism, Yosh, Shahar\nAli, 25, Toshkent</code>\n\n\U0001f4cc Orqaga: <b>\U0001f519 Orqaga</b>",
        "excel_process":"\u23f3 Excel yaratilmoqda...",
        "excel_success":"\u2705 Excel tayyor!",
        "excel_error":  "\u274c Excel yaratishda xatolik.",
        "wm_welcome":   "\U0001f5bc <b>Rasmga Matn</b>!\n\n\U0001f4f8 Avval rasm yuboring:",
        "wm_got_photo": "\u2705 Rasm qabul qilindi!\n\n\u270f\ufe0f Endi <b>matnni</b> yuboring:",
        "wm_process":   "\u23f3 Rasm tayyorlanmoqda...",
        "wm_success":   "\u2705 Rasm tayyor!",
        "wm_error":     "\u274c Xatolik yuz berdi.",
        "wm_no_photo":  "\u26a0\ufe0f Avval rasm yuboring!",
        "wm_only_photo":"\u26a0\ufe0f Faqat rasm yuboring.",
        "weather_btn":   "\U0001f324 Ob-havo",
        "weather_welcome":"\U0001f324 <b>Ob-havo</b>!\n\n\U0001f4cd Joylashuvingizni yuboring yoki shahar nomini yozing:\n\U0001f4cc Orqaga: <b>\U0001f519 Orqaga</b>",
        "weather_loading":"\u23f3 Ob-havo ma'lumoti olinmoqda...",
        "weather_error": "\u274c Shahar topilmadi. To'g'ri nom yozing.",
        "weather_api_err":"\u274c Ob-havo xizmati ishlamayapti. Keyinroq urinib ko'ring.",
    },
    "ru": {
        "sub_msg":      "\u26a0\ufe0f \u0414\u043b\u044f \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u044f \u043f\u043e\u0434\u043f\u0438\u0448\u0438\u0442\u0435\u0441\u044c \u043d\u0430 \u043a\u0430\u043d\u0430\u043b!",
        "sub_btn":      "\U0001f4e2 \u041f\u0435\u0440\u0435\u0439\u0442\u0438 \u043d\u0430 \u043a\u0430\u043d\u0430\u043b",
        "sub_check":    "\u2705 \u042f \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0441\u044f",
        "sub_error":    "\u274c \u0412\u044b \u0435\u0449\u0451 \u043d\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0438\u0441\u044c!",
        "sub_ok":       "\u2705 \u041f\u043e\u0434\u043f\u0438\u0441\u043a\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430!",
        "unsub_msg":    "\u26a0\ufe0f \u0412\u044b \u043e\u0442\u043f\u0438\u0441\u0430\u043b\u0438\u0441\u044c! \u041f\u043e\u0434\u043f\u0438\u0448\u0438\u0442\u0435\u0441\u044c \u0441\u043d\u043e\u0432\u0430.",
        "welcome":      "\U0001f44b \u041f\u0440\u0438\u0432\u0435\u0442, <b>{name}</b>!\n\n\U0001f916 \u042f <b>AI Javobchi</b> \u2014 \u0443\u043c\u043d\u044b\u0439 \u043c\u043d\u043e\u0433\u043e\u0444\u0443\u043d\u043a\u0446\u0438\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u0439 \u0431\u043e\u0442.\n\n\U0001f4cc \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u0430\u0437\u0434\u0435\u043b:",
        "ai_btn":       "\U0001f916 AI \u0427\u0430\u0442",
        "qr_btn":       "\U0001f4f7 QR \u041a\u043e\u0434",
        "pdf_btn":      "\U0001f4c4 PDF",
        "tts_btn":      "\U0001f399 \u0422\u0435\u043a\u0441\u0442 \u0432 \u0413\u043e\u043b\u043e\u0441",
        "excel_btn":    "\U0001f4ca Excel",
        "wm_btn":       "\U0001f5bc \u0422\u0435\u043a\u0441\u0442 \u043d\u0430 \u0424\u043e\u0442\u043e",
        "back_btn":     "\U0001f519 \u041d\u0430\u0437\u0430\u0434",
        "ai_welcome":   "\U0001f916 <b>AI \u0427\u0430\u0442</b>!\n\n\U0001f4ac \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0442\u0435\u043a\u0441\u0442, \u0444\u043e\u0442\u043e \u0438\u043b\u0438 \u0433\u043e\u043b\u043e\u0441.",
        "ai_thinking":  "\u23f3 \u0414\u0443\u043c\u0430\u044e...",
        "ai_error":     "\u274c \u041e\u0448\u0438\u0431\u043a\u0430. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0441\u043d\u043e\u0432\u0430.",
        "qr_welcome":   "\U0001f4f7 <b>QR \u041a\u043e\u0434</b>!\n\n\u270f\ufe0f \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0442\u0435\u043a\u0441\u0442 \u0438\u043b\u0438 \u0441\u0441\u044b\u043b\u043a\u0443.",
        "qr_success":   "\u2705 QR \u043a\u043e\u0434 \u0433\u043e\u0442\u043e\u0432!",
        "qr_error":     "\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u0438 QR.",
        "qr_only_text": "\u26a0\ufe0f \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0442\u043e\u043b\u044c\u043a\u043e <b>\u0442\u0435\u043a\u0441\u0442 \u0438\u043b\u0438 \u0441\u0441\u044b\u043b\u043a\u0443</b>.",
        "pdf_welcome":  "\U0001f4c4 <b>PDF \u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440</b>!\n\n\u270f\ufe0f \u041e\u0442\u043f\u0440\u0430\u0432\u043b\u044f\u0439\u0442\u0435 \u0442\u0435\u043a\u0441\u0442 \u043f\u043e \u0447\u0430\u0441\u0442\u044f\u043c.",
        "pdf_collect":  "\U0001f4dd \u041f\u043e\u043b\u0443\u0447\u0435\u043d\u043e! <b>{parts}</b> \u0447\u0430\u0441\u0442\u0435\u0439, <b>{chars}</b> \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432.\n\n\u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0435\u0442\u0435?",
        "pdf_done_btn": "\u2705 \u0421\u043e\u0437\u0434\u0430\u0442\u044c PDF",
        "pdf_undo_btn": "\u21a9\ufe0f \u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0435",
        "pdf_cleared":  "\u21a9\ufe0f \u041f\u043e\u0441\u043b\u0435\u0434\u043d\u044f\u044f \u0447\u0430\u0441\u0442\u044c \u0443\u0434\u0430\u043b\u0435\u043d\u0430.",
        "pdf_empty":    "\u26a0\ufe0f \u041d\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430.",
        "pdf_process":  "\u23f3 \u0421\u043e\u0437\u0434\u0430\u044e PDF...",
        "pdf_success":  "\u2705 PDF \u0433\u043e\u0442\u043e\u0432!",
        "pdf_error":    "\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u0438 PDF.",
        "tts_welcome":  "\U0001f399 <b>\u0422\u0435\u043a\u0441\u0442 \u0432 \u0413\u043e\u043b\u043e\u0441</b>!\n\n\u270f\ufe0f \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0442\u0435\u043a\u0441\u0442.",
        "tts_process":  "\u23f3 \u0421\u043e\u0437\u0434\u0430\u044e \u0430\u0443\u0434\u0438\u043e...",
        "tts_success":  "\u2705 \u0410\u0443\u0434\u0438\u043e \u0433\u043e\u0442\u043e\u0432\u043e!",
        "tts_error":    "\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u0438 \u0430\u0443\u0434\u0438\u043e.",
        "excel_welcome":"\U0001f4ca <b>Excel \u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440</b>!\n\n\u0424\u043e\u0440\u043c\u0430\u0442:\n<code>\u0418\u043c\u044f, \u0412\u043e\u0437\u0440\u0430\u0441\u0442, \u0413\u043e\u0440\u043e\u0434\n\u0410\u043b\u0438, 25, \u0422\u0430\u0448\u043a\u0435\u043d\u0442</code>",
        "excel_process":"\u23f3 \u0421\u043e\u0437\u0434\u0430\u044e Excel...",
        "excel_success":"\u2705 Excel \u0433\u043e\u0442\u043e\u0432!",
        "excel_error":  "\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u0438 Excel.",
        "wm_welcome":   "\U0001f5bc <b>\u0422\u0435\u043a\u0441\u0442 \u043d\u0430 \u0424\u043e\u0442\u043e</b>!\n\n\U0001f4f8 \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u043e\u0442\u043e:",
        "wm_got_photo": "\u2705 \u0424\u043e\u0442\u043e \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u043e!\n\n\u270f\ufe0f \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 <b>\u0442\u0435\u043a\u0441\u0442</b>:",
        "wm_process":   "\u23f3 \u041e\u0431\u0440\u0430\u0431\u0430\u0442\u044b\u0432\u0430\u044e...",
        "wm_success":   "\u2705 \u0424\u043e\u0442\u043e \u0433\u043e\u0442\u043e\u0432\u043e!",
        "wm_error":     "\u274c \u041e\u0448\u0438\u0431\u043a\u0430.",
        "wm_no_photo":  "\u26a0\ufe0f \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u043e\u0442\u043e!",
        "wm_only_photo":"\u26a0\ufe0f \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0442\u043e\u043b\u044c\u043a\u043e \u0444\u043e\u0442\u043e.",
        "weather_btn":   "\U0001f324 \u041f\u043e\u0433\u043e\u0434\u0430",
        "weather_welcome":"\U0001f324 <b>\u041f\u043e\u0433\u043e\u0434\u0430</b>!\n\n\U0001f4cd \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0433\u0435\u043e\u043b\u043e\u043a\u0430\u0446\u0438\u044e \u0438\u043b\u0438 \u043d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0433\u043e\u0440\u043e\u0434\u0430.",
        "weather_loading":"\u23f3 \u041f\u043e\u043b\u0443\u0447\u0430\u044e \u0434\u0430\u043d\u043d\u044b\u0435...",
        "weather_error": "\u274c \u0413\u043e\u0440\u043e\u0434 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.",
        "weather_api_err":"\u274c \u0421\u0435\u0440\u0432\u0438\u0441 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d.",
    },
    "en": {
        "sub_msg":      "\u26a0\ufe0f Subscribe to our channel to use the bot!",
        "sub_btn":      "\U0001f4e2 Go to Channel",
        "sub_check":    "\u2705 I subscribed",
        "sub_error":    "\u274c You haven't subscribed yet! Please subscribe first.",
        "sub_ok":       "\u2705 Subscription confirmed! Welcome!",
        "unsub_msg":    "\u26a0\ufe0f You left the channel! Subscribe again to continue.",
        "welcome":      "\U0001f44b Hello, <b>{name}</b>!\n\n\U0001f916 I am <b>AI Javobchi</b> \u2014 a powerful multi-function AI bot.\n\n\U0001f4cc Choose a section:",
        "ai_btn":       "\U0001f916 AI Chat",
        "qr_btn":       "\U0001f4f7 QR Code",
        "pdf_btn":      "\U0001f4c4 PDF",
        "tts_btn":      "\U0001f399 Text to Speech",
        "excel_btn":    "\U0001f4ca Excel",
        "wm_btn":       "\U0001f5bc Image Text",
        "back_btn":     "\U0001f519 Back",
        "ai_welcome":   "\U0001f916 <b>AI Chat</b> activated!\n\n\U0001f4ac Send text, image or voice.",
        "ai_thinking":  "\u23f3 Thinking...",
        "ai_error":     "\u274c An error occurred. Please try again.",
        "qr_welcome":   "\U0001f4f7 <b>QR Code</b> Generator!\n\n\u270f\ufe0f Send text or a link.",
        "qr_success":   "\u2705 QR code ready!",
        "qr_error":     "\u274c Error creating QR code.",
        "qr_only_text": "\u26a0\ufe0f Please send only <b>text or a link</b>.",
        "pdf_welcome":  "\U0001f4c4 <b>PDF Generator</b>!\n\n\u270f\ufe0f Send text in parts then create PDF.",
        "pdf_collect":  "\U0001f4dd Received! <b>{parts}</b> parts, <b>{chars}</b> chars.\n\nContinue?",
        "pdf_done_btn": "\u2705 Create PDF",
        "pdf_undo_btn": "\u21a9\ufe0f Remove last",
        "pdf_cleared":  "\u21a9\ufe0f Last part removed.",
        "pdf_empty":    "\u26a0\ufe0f No text yet.",
        "pdf_process":  "\u23f3 Creating PDF...",
        "pdf_success":  "\u2705 PDF ready!",
        "pdf_error":    "\u274c Error creating PDF.",
        "tts_welcome":  "\U0001f399 <b>Text to Speech</b>!\n\n\u270f\ufe0f Send text.",
        "tts_process":  "\u23f3 Creating audio...",
        "tts_success":  "\u2705 Audio ready!",
        "tts_error":    "\u274c Error creating audio.",
        "excel_welcome":"\U0001f4ca <b>Excel Generator</b>!\n\nFormat:\n<code>Name, Age, City\nAli, 25, Tashkent</code>",
        "excel_process":"\u23f3 Creating Excel...",
        "excel_success":"\u2705 Excel ready!",
        "excel_error":  "\u274c Error creating Excel.",
        "wm_welcome":   "\U0001f5bc <b>Image Text</b>!\n\n\U0001f4f8 First send a photo:",
        "wm_got_photo": "\u2705 Photo received!\n\n\u270f\ufe0f Now send the <b>text</b>:",
        "wm_process":   "\u23f3 Processing image...",
        "wm_success":   "\u2705 Image ready!",
        "wm_error":     "\u274c An error occurred.",
        "wm_no_photo":  "\u26a0\ufe0f Send a photo first!",
        "wm_only_photo":"\u26a0\ufe0f Please send a photo only.",
        "weather_btn":   "\U0001f324 Weather",
        "weather_welcome":"\U0001f324 <b>Weather</b>!\n\n\U0001f4cd Send your location or type a city name.",
        "weather_loading":"\u23f3 Getting weather data...",
        "weather_error": "\u274c City not found. Try again.",
        "weather_api_err":"\u274c Weather service unavailable.",
    }
}

BACK_TEXTS = ["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]

def kb_lang():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\U0001f1fa\U0001f1ff O'zbek"), KeyboardButton(text="\U0001f1f7\U0001f1fa \u0420\u0443\u0441\u0441\u043a\u0438\u0439")],
        [KeyboardButton(text="\U0001f1ec\U0001f1e7 English")]
    ], resize_keyboard=True)

def kb_main(lang):
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=T[lang]["ai_btn"])],
        [KeyboardButton(text=T[lang]["qr_btn"]), KeyboardButton(text=T[lang]["pdf_btn"])],
        [KeyboardButton(text=T[lang]["tts_btn"]), KeyboardButton(text=T[lang]["excel_btn"])],
        [KeyboardButton(text=T[lang]["wm_btn"]), KeyboardButton(text=T[lang]["weather_btn"])]
    ], resize_keyboard=True)

def kb_back(lang):
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=T[lang]["back_btn"])]
    ], resize_keyboard=True)

def kb_subscribe(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=T[lang]["sub_btn"], url="https://t.me/uzinnotech")],
        [InlineKeyboardButton(text=T[lang]["sub_check"], callback_data=f"sub_{lang}")]
    ])

async def get_lang(state):
    d = await state.get_data()
    return d.get("language", "uz")

async def is_subscribed(user_id):
    try:
        m = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return m.status not in ["left", "kicked", "banned"]
    except Exception:
        return True

async def check_sub(message, state):
    if not await is_subscribed(message.from_user.id):
        lang = await get_lang(state)
        await message.answer(T[lang]["unsub_msg"], reply_markup=kb_subscribe(lang))
        return False
    return True

async def send_chunks(message, text):
    for i in range(0, len(text), 4000):
        await message.answer(text[i:i+4000])

def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def setup_pdf_font(pdf, size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                pdf.add_font("UniFont", "", p, uni=True)
                pdf.set_font("UniFont", size=size)
                return True
            except Exception:
                pass
    pdf.set_font("Helvetica", size=size)
    return False

async def ai_text_req(messages, lang):
    system = {
        "uz": "Sen aqlli AI assistantsan. O'zbek tilida aniq va foydali javob ber.",
        "ru": "\u0422\u044b \u0443\u043c\u043d\u044b\u0439 AI \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442. \u041e\u0442\u0432\u0435\u0447\u0430\u0439 \u043f\u043e-\u0440\u0443\u0441\u0441\u043a\u0438.",
        "en": "You are a smart AI assistant. Answer clearly in English."
    }.get(lang, "You are a helpful AI assistant.")
    try:
        async with aiohttp.ClientSession() as sess:
            r = await sess.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "system", "content": system}, *messages],
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
            if r.status == 200:
                d = await r.json()
                return d["choices"][0]["message"]["content"]
    except Exception as e:
        log.error(f"Groq error: {e}")
    return None

async def ai_vision_req(image_bytes, prompt, lang):
    sys_p = {
        "uz": "Rasmni batafsil tahlil qil. O'zbek tilida javob ber.",
        "ru": "\u041f\u043e\u0434\u0440\u043e\u0431\u043d\u043e \u043f\u0440\u043e\u0430\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u0443\u0439 \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435. \u041e\u0442\u0432\u0435\u0447\u0430\u0439 \u043f\u043e-\u0440\u0443\u0441\u0441\u043a\u0438.",
        "en": "Analyze the image in detail. Answer in English."
    }.get(lang, "Analyze the image.")
    try:
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")
        async with aiohttp.ClientSession() as sess:
            r = await sess.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": sys_p + "\n\n" + (prompt or "Bu rasmda nima bor? Batafsil tushuntir.")},
                            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                        ]
                    }],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
            if r.status == 200:
                d = await r.json()
                return d["candidates"][0]["content"]["parts"][0]["text"]
            else:
                err = await r.text()
                log.error(f"Gemini {r.status}: {err}")
    except Exception as e:
        log.error(f"Gemini error: {e}")
    return None

async def ai_voice_req(audio_bytes):
    try:
        async with aiohttp.ClientSession() as sess:
            form = aiohttp.FormData()
            form.add_field("file", audio_bytes, filename="voice.ogg", content_type="audio/ogg")
            form.add_field("model", "whisper-large-v3")
            r = await sess.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                data=form,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            if r.status == 200:
                d = await r.json()
                return d.get("text", "")
    except Exception as e:
        log.error(f"Whisper error: {e}")
    return None

@dp.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    uid = str(msg.from_user.id)
    users_db[uid] = {
        "name": msg.from_user.full_name,
        "username": f"@{msg.from_user.username}" if msg.from_user.username else "\u2014",
        "lang": users_db.get(uid, {}).get("lang", "\u2014"),
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "count": users_db.get(uid, {}).get("count", 0) + 1
    }
    db_save(users_db)
    await state.set_state(S.lang)
    await msg.answer(
        "\U0001f44b Assalomu alaykum! / \u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439\u0442\u0435! / Hello!\n\n\U0001f310 Tilni tanlang / \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u044f\u0437\u044b\u043a / Choose language:",
        reply_markup=kb_lang()
    )

@dp.message(S.lang)
async def choose_lang(msg: Message, state: FSMContext):
    # Faqat bayroq emoji orqali til tanlanadi
    t = msg.text or ""
    if "\U0001f1fa\U0001f1ff" in t: lang = "uz"
    elif "\U0001f1f7\U0001f1fa" in t: lang = "ru"
    elif "\U0001f1ec\U0001f1e7" in t: lang = "en"
    else:
        await msg.answer("Iltimos, til tugmasini bosing:", reply_markup=kb_lang())
        return
    await state.update_data(language=lang)
    uid = str(msg.from_user.id)
    if uid in users_db:
        users_db[uid]["lang"] = lang
        db_save(users_db)
    if not await is_subscribed(msg.from_user.id):
        await msg.answer(T[lang]["sub_msg"], reply_markup=kb_subscribe(lang))
        return
    await state.set_state(S.menu)
    await msg.answer(T[lang]["welcome"].format(name=msg.from_user.first_name), reply_markup=kb_main(lang), parse_mode="HTML")

@dp.callback_query(F.data.startswith("sub_"))
async def cb_sub(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split("_")[1]
    if await is_subscribed(cb.from_user.id):
        await state.update_data(language=lang)
        await state.set_state(S.menu)
        await cb.message.answer(T[lang]["sub_ok"], reply_markup=kb_main(lang))
        await cb.answer("\u2705")
    else:
        await cb.answer(T[lang]["sub_error"], show_alert=True)

@dp.message(F.text.in_(["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]))
async def go_back(msg: Message, state: FSMContext):
    cur = await state.get_state()
    if cur == S.lang:
        return
    lang = await get_lang(state)
    await state.update_data(chat_history=[], pdf_parts=[], pdf_msg_ids=[], pdf_prompt_ids=[], wm_photo_id=None, weather=None)
    await state.set_state(S.menu)
    await msg.answer(T[lang]["welcome"].format(name=msg.from_user.first_name), reply_markup=kb_main(lang), parse_mode="HTML")

@dp.message(Command("stats"))
async def cmd_stats(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    total = len(users_db)
    langs = {"uz": 0, "ru": 0, "en": 0}
    for u in users_db.values():
        l = u.get("lang", "\u2014")
        langs[l] = langs.get(l, 0) + 1
    last = list(users_db.items())[-10:]
    last_txt = ""
    for uid, u in reversed(last):
        last_txt += f"\n\u2022 {u['name']} {u['username']} [{u['lang']}] \u2014 {u['date']}"
    await msg.answer(
        f"\U0001f4ca <b>Bot Statistikasi</b>\n\n"
        f"\U0001f465 Jami: <b>{total}</b>\n\n"
        f"\U0001f310 Tillar:\n"
        f"  \U0001f1fa\U0001f1ff O'zbek: <b>{langs.get('uz',0)}</b>\n"
        f"  \U0001f1f7\U0001f1fa Rus: <b>{langs.get('ru',0)}</b>\n"
        f"  \U0001f1ec\U0001f1e7 Ingliz: <b>{langs.get('en',0)}</b>\n\n"
        f"\U0001f550 So'nggi 10:{last_txt}",
        parse_mode="HTML"
    )

# AI CHAT
@dp.message(F.text.in_(["\U0001f916 AI Suhbat", "\U0001f916 AI \u0427\u0430\u0442", "\U0001f916 AI Chat"]))
async def ai_start(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    await state.set_state(S.ai_chat)
    await state.update_data(chat_history=[])
    await msg.answer(T[lang]["ai_welcome"], reply_markup=kb_back(lang), parse_mode="HTML")

@dp.message(S.ai_chat, F.text)
async def ai_text_handler(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    if msg.text in ["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]: return
    lang = await get_lang(state)
    data = await state.get_data()
    history = data.get("chat_history", [])
    wait = await msg.answer(T[lang]["ai_thinking"])
    history.append({"role": "user", "content": msg.text})
    if len(history) > 20: history = history[-20:]
    reply = await ai_text_req(history, lang)
    await wait.delete()
    if reply:
        history.append({"role": "assistant", "content": reply})
        await state.update_data(chat_history=history)
        await send_chunks(msg, reply)
    else:
        await msg.answer(T[lang]["ai_error"])

@dp.message(S.ai_chat, F.photo)
async def ai_photo_handler(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    wait = await msg.answer(T[lang]["ai_thinking"])
    try:
        file = await bot.get_file(msg.photo[-1].file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        out.seek(0)
        reply = await ai_vision_req(out.read(), msg.caption or "", lang)
        await wait.delete()
        if reply:
            await send_chunks(msg, reply)
        else:
            await msg.answer(T[lang]["ai_error"])
    except Exception as e:
        log.error(f"AI photo: {e}")
        await wait.delete()
        await msg.answer(T[lang]["ai_error"])

@dp.message(S.ai_chat, F.voice)
async def ai_voice_handler(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    wait = await msg.answer(T[lang]["ai_thinking"])
    try:
        file = await bot.get_file(msg.voice.file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        text = await ai_voice_req(buf.getvalue())
        if not text:
            await wait.delete()
            await msg.answer(T[lang]["ai_error"])
            return
        data = await state.get_data()
        history = data.get("chat_history", [])
        history.append({"role": "user", "content": text})
        if len(history) > 20: history = history[-20:]
        reply = await ai_text_req(history, lang)
        await wait.delete()
        if reply:
            history.append({"role": "assistant", "content": reply})
            await state.update_data(chat_history=history)
            await msg.answer(f"\U0001f3a4 <i>{text}</i>", parse_mode="HTML")
            await send_chunks(msg, reply)
        else:
            await msg.answer(T[lang]["ai_error"])
    except Exception as e:
        log.error(f"AI voice: {e}")
        await wait.delete()
        await msg.answer(T[lang]["ai_error"])

# QR
@dp.message(F.text.in_(["\U0001f4f7 QR Kod", "\U0001f4f7 QR \u041a\u043e\u0434", "\U0001f4f7 QR Code"]))
async def qr_start(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    await state.set_state(S.qr)
    await msg.answer(T[lang]["qr_welcome"], reply_markup=kb_back(lang), parse_mode="HTML")

@dp.message(S.qr, F.text)
async def qr_create(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    if msg.text in ["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]: return
    lang = await get_lang(state)
    try:
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
        qr.add_data(msg.text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        await msg.answer_photo(BufferedInputFile(buf.read(), "qr.png"), caption=T[lang]["qr_success"])
    except Exception as e:
        log.error(f"QR: {e}")
        await msg.answer(T[lang]["qr_error"])

@dp.message(S.qr, ~F.text)
async def qr_wrong(msg: Message, state: FSMContext):
    lang = await get_lang(state)
    await msg.answer(T[lang]["qr_only_text"], parse_mode="HTML")

# PDF
@dp.message(F.text.in_(["\U0001f4c4 PDF"]))
async def pdf_start(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    await state.set_state(S.pdf)
    await state.update_data(pdf_parts=[], pdf_msg_ids=[], pdf_prompt_ids=[])
    await msg.answer(T[lang]["pdf_welcome"], reply_markup=kb_back(lang), parse_mode="HTML")

@dp.message(S.pdf, F.text)
async def pdf_collect(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    if msg.text in ["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]: return
    lang = await get_lang(state)
    data = await state.get_data()
    parts = data.get("pdf_parts", [])
    msg_ids = data.get("pdf_msg_ids", [])
    prompt_ids = data.get("pdf_prompt_ids", [])
    parts.append(msg.text)
    msg_ids.append(msg.message_id)
    for pid in prompt_ids:
        try: await bot.delete_message(msg.chat.id, pid)
        except: pass
    total_chars = sum(len(p) for p in parts)
    caption = T[lang]["pdf_collect"].format(parts=len(parts), chars=total_chars)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=T[lang]["pdf_done_btn"], callback_data="pdf_create"),
         InlineKeyboardButton(text=T[lang]["pdf_undo_btn"], callback_data="pdf_undo")]
    ])
    prompt = await msg.answer(caption, reply_markup=markup, parse_mode="HTML")
    await state.update_data(pdf_parts=parts, pdf_msg_ids=msg_ids, pdf_prompt_ids=[prompt.message_id])

@dp.callback_query(F.data == "pdf_undo")
async def pdf_undo(cb: CallbackQuery, state: FSMContext):
    lang = await get_lang(state)
    data = await state.get_data()
    parts = data.get("pdf_parts", [])
    msg_ids = data.get("pdf_msg_ids", [])
    if not parts:
        await cb.answer(T[lang]["pdf_empty"])
        return
    parts.pop()
    if msg_ids:
        try: await bot.delete_message(cb.message.chat.id, msg_ids.pop())
        except: pass
    try: await cb.message.delete()
    except: pass
    await state.update_data(pdf_parts=parts, pdf_msg_ids=msg_ids, pdf_prompt_ids=[])
    await cb.answer()
    if parts:
        total_chars = sum(len(p) for p in parts)
        caption = T[lang]["pdf_collect"].format(parts=len(parts), chars=total_chars)
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=T[lang]["pdf_done_btn"], callback_data="pdf_create"),
             InlineKeyboardButton(text=T[lang]["pdf_undo_btn"], callback_data="pdf_undo")]
        ])
        p = await cb.message.answer(caption, reply_markup=markup, parse_mode="HTML")
        await state.update_data(pdf_prompt_ids=[p.message_id])
    else:
        await cb.message.answer(T[lang]["pdf_cleared"])

@dp.callback_query(F.data == "pdf_create")
async def pdf_create(cb: CallbackQuery, state: FSMContext):
    lang = await get_lang(state)
    data = await state.get_data()
    parts = data.get("pdf_parts", [])
    prompt_ids = data.get("pdf_prompt_ids", [])
    if not parts:
        await cb.answer(T[lang]["pdf_empty"])
        return
    for pid in prompt_ids:
        try: await bot.delete_message(cb.message.chat.id, pid)
        except: pass
    try: await cb.message.delete()
    except: pass
    await cb.answer()
    full_text = "\n".join(parts)
    wait = await cb.message.answer(T[lang]["pdf_process"])
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_margins(20, 20, 20)
        uni = setup_pdf_font(pdf, 12)
        if not uni:
            full_text = unicodedata.normalize("NFKD", full_text).encode("ascii", "ignore").decode("ascii")
        pdf.set_font_size(20)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 12, "Document", ln=True, align="C")
        pdf.ln(2)
        pdf.set_draw_color(80, 80, 80)
        pdf.set_line_width(0.4)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)
        pdf.set_font_size(9)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 6, datetime.now().strftime("%d.%m.%Y %H:%M"), ln=True, align="R")
        pdf.ln(4)
        pdf.set_font_size(11)
        pdf.set_text_color(30, 30, 30)
        for line in full_text.split("\n"):
            pdf.multi_cell(0, 7, line if line else " ")
        pdf.set_y(-15)
        pdf.set_font_size(9)
        pdf.set_text_color(160, 160, 160)
        pdf.cell(0, 10, f"Page {pdf.page_no()}", align="C")
        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        await wait.delete()
        await cb.message.answer_document(BufferedInputFile(buf.read(), "document.pdf"), caption=T[lang]["pdf_success"])
        await state.update_data(pdf_parts=[], pdf_msg_ids=[], pdf_prompt_ids=[])
        await cb.message.answer(T[lang]["pdf_welcome"], reply_markup=kb_back(lang), parse_mode="HTML")
    except Exception as e:
        log.error(f"PDF: {e}")
        try: await wait.delete()
        except: pass
        await cb.message.answer(T[lang]["pdf_error"])

# TTS
@dp.message(F.text.in_(["\U0001f399 Matndan Ovoz", "\U0001f399 \u0422\u0435\u043a\u0441\u0442 \u0432 \u0413\u043e\u043b\u043e\u0441", "\U0001f399 Text to Speech"]))
async def tts_start(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    await state.set_state(S.tts)
    await msg.answer(T[lang]["tts_welcome"], reply_markup=kb_back(lang), parse_mode="HTML")

@dp.message(S.tts, F.text)
async def tts_create(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    if msg.text in ["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]: return
    lang = await get_lang(state)
    wait = await msg.answer(T[lang]["tts_process"])
    try:
        lang_map = {"uz": "tr", "ru": "ru", "en": "en"}
        def _make():
            tts = gTTS(text=msg.text, lang=lang_map.get(lang, "en"))
            b = io.BytesIO()
            tts.write_to_fp(b)
            b.seek(0)
            return b.read()
        audio = await asyncio.get_running_loop().run_in_executor(None, _make)
        await wait.delete()
        await msg.answer_audio(BufferedInputFile(audio, "voice.mp3"), caption=T[lang]["tts_success"])
    except Exception as e:
        log.error(f"TTS: {e}")
        try: await wait.delete()
        except: pass
        await msg.answer(T[lang]["tts_error"])

# EXCEL
@dp.message(F.text.in_(["\U0001f4ca Excel"]))
async def excel_start(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    await state.set_state(S.excel)
    await msg.answer(T[lang]["excel_welcome"], reply_markup=kb_back(lang), parse_mode="HTML")

@dp.message(S.excel, F.text)
async def excel_create(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    if msg.text in ["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]: return
    lang = await get_lang(state)
    wait = await msg.answer(T[lang]["excel_process"])
    try:
        rows = []
        for line in msg.text.strip().split("\n"):
            line = line.strip()
            if not line: continue
            if "," in line: row = [c.strip() for c in line.split(",")]
            elif "\t" in line: row = [c.strip() for c in line.split("\t")]
            else: row = [line]
            rows.append(row)
        buf = io.BytesIO()
        buf.write(codecs.BOM_UTF8)
        s = io.StringIO()
        csv.writer(s).writerows(rows)
        buf.write(s.getvalue().encode("utf-8"))
        buf.seek(0)
        await wait.delete()
        await msg.answer_document(BufferedInputFile(buf.read(), "data.csv"), caption=T[lang]["excel_success"])
    except Exception as e:
        log.error(f"Excel: {e}")
        try: await wait.delete()
        except: pass
        await msg.answer(T[lang]["excel_error"])

# WATERMARK
@dp.message(F.text.in_(["\U0001f5bc Rasmga Matn", "\U0001f5bc \u0422\u0435\u043a\u0441\u0442 \u043d\u0430 \u0424\u043e\u0442\u043e", "\U0001f5bc Image Text"]))
async def wm_start(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    await state.set_state(S.wm_photo)
    await state.update_data(wm_photo_id=None)
    await msg.answer(T[lang]["wm_welcome"], reply_markup=kb_back(lang), parse_mode="HTML")

@dp.message(S.wm_photo, F.photo)
async def wm_got_photo(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    await state.update_data(wm_photo_id=msg.photo[-1].file_id)
    await state.set_state(S.wm_text)
    await msg.answer(T[lang]["wm_got_photo"], parse_mode="HTML")

@dp.message(S.wm_photo, ~F.photo & ~F.text)
async def wm_wrong(msg: Message, state: FSMContext):
    lang = await get_lang(state)
    await msg.answer(T[lang]["wm_only_photo"], parse_mode="HTML")

@dp.message(S.wm_text, F.text)
async def wm_apply(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    if msg.text in ["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]: return
    lang = await get_lang(state)
    data = await state.get_data()
    photo_id = data.get("wm_photo_id")
    if not photo_id:
        await msg.answer(T[lang]["wm_no_photo"])
        await state.set_state(S.wm_photo)
        return
    wait = await msg.answer(T[lang]["wm_process"])
    try:
        file = await bot.get_file(photo_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        buf.seek(0)
        img = Image.open(buf).convert("RGBA")
        w, h = img.size
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        font_size = max(24, w // 18)
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), msg.text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x, y = (w-tw)//2, (h-th)//2
        draw.text((x+3, y+3), msg.text, font=font, fill=(0,0,0,100))
        draw.text((x, y), msg.text, font=font, fill=(255,255,255,210))
        result = Image.alpha_composite(img, layer).convert("RGB")
        out = io.BytesIO()
        result.save(out, format="JPEG", quality=92)
        out.seek(0)
        await wait.delete()
        await msg.answer_photo(BufferedInputFile(out.read(), "image.jpg"), caption=T[lang]["wm_success"])
        await state.update_data(wm_photo_id=None)
        await state.set_state(S.wm_photo)
        await msg.answer(T[lang]["wm_welcome"], parse_mode="HTML")
    except Exception as e:
        log.error(f"Watermark: {e}")
        try: await wait.delete()
        except: pass
        await msg.answer(T[lang]["wm_error"])

# ─── WEATHER ─────────────────────────────────────────────────────────────────
WEATHER_EMOJIS = {
    "Clear": "\u2600\ufe0f", "Clouds": "\u26c5", "Rain": "\U0001f327\ufe0f",
    "Drizzle": "\U0001f327\ufe0f", "Thunderstorm": "\u26a1", "Snow": "\u2744\ufe0f",
    "Mist": "\U0001f32b\ufe0f", "Fog": "\U0001f32b\ufe0f", "Haze": "\U0001f32b\ufe0f",
    "Smoke": "\U0001f32b\ufe0f", "Dust": "\U0001f32b\ufe0f", "Sand": "\U0001f32b\ufe0f",
    "Ash": "\U0001f32b\ufe0f", "Squall": "\U0001f4a8", "Tornado": "\U0001f32a\ufe0f"
}

WIND_DIR = {
    "uz": ["Shimol", "Shimoli-sharq", "Sharq", "Janubi-sharq", "Janub", "Janubi-g'arb", "G'arb", "Shimoli-g'arb"],
    "ru": ["\u0421", "\u0421\u0412", "\u0412", "\u042e\u0412", "\u042e", "\u042e\u0417", "\u0417", "\u0421\u0417"],
    "en": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
}

def wind_direction(deg, lang):
    dirs = WIND_DIR.get(lang, WIND_DIR["en"])
    return dirs[round(deg / 45) % 8]

def format_weather(data, lang, city_override=None):
    city    = city_override or data.get("name", "")
    country = data.get("sys", {}).get("country", "")
    temp    = round(data["main"]["temp"])
    feels   = round(data["main"]["feels_like"])
    hum     = data["main"]["humidity"]
    press   = data["main"]["pressure"]
    wind_s  = round(data["wind"]["speed"])
    wind_d  = wind_direction(data["wind"].get("deg", 0), lang)
    vis     = data.get("visibility", 0) // 1000
    weather = data["weather"][0]
    desc    = weather["description"].capitalize()
    main_w  = weather["main"]
    emoji   = WEATHER_EMOJIS.get(main_w, "\U0001f324")

    sunrise = datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M")
    sunset  = datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M")

    if lang == "uz":
        return (
            f"{emoji} <b>{city}, {country}</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\U0001f321\ufe0f Harorat: <b>{temp}°C</b> (his qilish: {feels}°C)\n"
            f"\U0001f4ac Holat: <b>{desc}</b>\n"
            f"\U0001f4a7 Namlik: <b>{hum}%</b>\n"
            f"\U0001f4a8 Shamol: <b>{wind_s} m/s</b> ({wind_d})\n"
            f"\U0001f321\ufe0f Bosim: <b>{press} hPa</b>\n"
            f"\U0001f440 Ko'rinish: <b>{vis} km</b>\n"
            f"\u2600\ufe0f Quyosh: {sunrise} \u2015 {sunset}\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\U0001f557 {datetime.now().strftime('%H:%M, %d.%m.%Y')}"
        )
    elif lang == "ru":
        return (
            f"{emoji} <b>{city}, {country}</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\U0001f321\ufe0f \u0422\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430: <b>{temp}°C</b> (\u043e\u0449\u0443\u0449\u0430\u0435\u0442\u0441\u044f: {feels}°C)\n"
            f"\U0001f4ac \u0421\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435: <b>{desc}</b>\n"
            f"\U0001f4a7 \u0412\u043b\u0430\u0436\u043d\u043e\u0441\u0442\u044c: <b>{hum}%</b>\n"
            f"\U0001f4a8 \u0412\u0435\u0442\u0435\u0440: <b>{wind_s} \u043c/\u0441</b> ({wind_d})\n"
            f"\U0001f321\ufe0f \u0414\u0430\u0432\u043b\u0435\u043d\u0438\u0435: <b>{press} \u0433\u041f\u0430</b>\n"
            f"\U0001f440 \u0412\u0438\u0434\u0438\u043c\u043e\u0441\u0442\u044c: <b>{vis} \u043a\u043c</b>\n"
            f"\u2600\ufe0f \u0420\u0430\u0441\u0441\u0432\u0435\u0442: {sunrise} \u2015 {sunset}\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\U0001f557 {datetime.now().strftime('%H:%M, %d.%m.%Y')}"
        )
    else:
        return (
            f"{emoji} <b>{city}, {country}</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\U0001f321\ufe0f Temperature: <b>{temp}°C</b> (feels like {feels}°C)\n"
            f"\U0001f4ac Condition: <b>{desc}</b>\n"
            f"\U0001f4a7 Humidity: <b>{hum}%</b>\n"
            f"\U0001f4a8 Wind: <b>{wind_s} m/s</b> ({wind_d})\n"
            f"\U0001f321\ufe0f Pressure: <b>{press} hPa</b>\n"
            f"\U0001f440 Visibility: <b>{vis} km</b>\n"
            f"\u2600\ufe0f Sunrise: {sunrise} \u2015 {sunset}\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\U0001f557 {datetime.now().strftime('%H:%M, %d.%m.%Y')}"
        )

async def get_weather_by_city(city: str):
    try:
        async with aiohttp.ClientSession() as sess:
            r = await sess.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": WEATHER_KEY, "units": "metric", "lang": "ru"},
                timeout=aiohttp.ClientTimeout(total=10)
            )
            if r.status == 200:
                return await r.json()
            return None
    except Exception as e:
        log.error(f"Weather city error: {e}")
        return None

async def get_weather_by_coords(lat: float, lon: float):
    try:
        async with aiohttp.ClientSession() as sess:
            r = await sess.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "appid": WEATHER_KEY, "units": "metric", "lang": "ru"},
                timeout=aiohttp.ClientTimeout(total=10)
            )
            if r.status == 200:
                return await r.json()
            return None
    except Exception as e:
        log.error(f"Weather coords error: {e}")
        return None

@dp.message(F.text.in_(["\U0001f324 Ob-havo", "\U0001f324 \u041f\u043e\u0433\u043e\u0434\u0430", "\U0001f324 Weather"]))
async def weather_start(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    await state.clear()
    await state.update_data(language=lang)
    await state.set_state(S.weather)
    loc_text = {
        "uz": "\U0001f4cd Joylashuvimni yuborish",
        "ru": "\U0001f4cd \u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0433\u0435\u043e\u043b\u043e\u043a\u0430\u0446\u0438\u044e",
        "en": "\U0001f4cd Send my location"
    }.get(lang, "\U0001f4cd Send my location")
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=loc_text, request_location=True)],
        [KeyboardButton(text=T[lang]["back_btn"])]
    ], resize_keyboard=True)
    await msg.answer(T[lang]["weather_welcome"], reply_markup=kb, parse_mode="HTML")

@dp.message(S.weather, F.location)
async def weather_by_location(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    lang = await get_lang(state)
    wait = await msg.answer(T[lang]["weather_loading"])
    data = await get_weather_by_coords(msg.location.latitude, msg.location.longitude)
    await wait.delete()
    if data:
        await msg.answer(format_weather(data, lang), parse_mode="HTML")
    else:
        await msg.answer(T[lang]["weather_api_err"])

@dp.message(S.weather, F.text)
async def weather_by_city(msg: Message, state: FSMContext):
    if not await check_sub(msg, state): return
    if msg.text in ["\U0001f519 Orqaga", "\U0001f519 \u041d\u0430\u0437\u0430\u0434", "\U0001f519 Back"]: return
    lang = await get_lang(state)
    wait = await msg.answer(T[lang]["weather_loading"])
    data = await get_weather_by_city(msg.text.strip())
    await wait.delete()
    if data:
        await msg.answer(format_weather(data, lang), parse_mode="HTML")
    else:
        await msg.answer(T[lang]["weather_error"])

async def main():
    log.info("Bot ishga tushdi!")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
