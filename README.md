# 🤖 Javobchi AI & Universal Converter Bot

Telegram bot — Universal fayl konvertatsiya, AI suhbat, video yuklab olish, inline o'yinlar va ko'p-botli (Multi-Bot) rejim. Python + Aiogram 3, Vercel serverless deployment.

## ✨ Barcha Funksiyalar

### 📁 Universal Fayl Transfer (55+ format)
| Turkum | Konversiyalar |
|---|---|
| 🖼 Rasmlar | PNG ↔ JPG, WEBP, BMP, TIFF, ICO · HEIC → JPG |
| 📄 Hujjatlar | DOCX → PDF, TXT, HTML · PDF → TXT, DOCX, PNG · TXT → PDF, DOCX · MD → HTML, PDF · HTML → PDF |
| 📊 Jadvallar | XLSX ↔ CSV, JSON · XLS → XLSX · CSV ↔ JSON · XLSX → PDF |
| 🎥 Video & Audio | MP4, AVI, MOV, MKV, WEBM → **GIF** (8 sek), **MP3**, **OGG** (voice), **WAV**, **M4A** |
| 💾 Data | JSON ↔ XML ↔ YAML |
| 📦 Arxivlar | ZIP ↔ TAR, 7Z · 7Z, TAR, GZ → ZIP |
| 📚 E-Kitoblar | EPUB → TXT, PDF |

### 🤖 AI Suhbat va Web Tahlil
- **Kontekstli Suhbat (Multi-Turn Chat)** — AI avvalgi savol va javoblaringizni eslab qoladi va haqiqiy ChatGPT/Claude kabi suhbat olib boradi
- **`/clear` / `/newchat`** — Suhbat xotirasini tozalab, yangi mavzu boshlash buyrug'i
- **Groq (GPT-OSS 120B / Qwen / Compound)** va **Gemini** orqali o'ta tezkor AI javoblar
- **Multi-API Key Rotator** — 429 rate limit bo'lganda avtomatik zaxira kalitga o'tadi
- Veb-sahifa havolasi yuborilsa — AI mazmunini qisqartiradi (summary)
- Bot javob tayyorlayotganda **"yozyapti..."** holati ko'rsatiladi

### 🎬 Video Yuklab Olish
- **YouTube, Instagram Reels, TikTok, Twitter/X, Facebook** havolasidan video yuklab olish
- Inline rejimda ham ishlaydi (`@botusername link`)

### 🎮 Inline O'yinlar (Telegram Games Platform)
- **🐍 Snake Game** — Klassik ilon o'yini, mobil touch/swipe boshqaruv
- **🎮 2048 Game** — Raqam birlashtiruvchi boshqoturv, mobil moslashtirilgan
- Istalgan chatda `@botusername` deb yozib o'ynash mumkin

### 🔤 Unicode Font Stilizatsiyasi
- `/font Bold Salom` — 12 xil chiroyli Unicode font uslubi
- Bold, Script, Gothic, Bubble, Double, Monospace, Small Caps, Fraktur, Outline, Squared, Circled

### 🌐 3 Tilli Qo'llab-Quvvatlash
- 🇺🇿 O'zbekcha, 🇷🇺 Русский, 🇬🇧 English
- Birinchi kirganda til tanlash, istalgan vaqtda o'zgartirish

### 🤖 Multi-Bot Rejimi
- **Bitta kod bazasi — bir nechta bot** bir vaqtda parallel ishlaydi
- Har bir bot o'z nomidan javob beradi (aralashmaydi)
- Token qo'shish/olib tashlash — kodni o'zgartirmasdan, faqat env variable'ni tahrirlash

### 📊 Supabase Logging & Analytics
- Har bir foydalanuvchi harakati `activities` jadvalida loglanadi
- **FIFO Auto-Pruner** — 2000 ta logdan oshsa eng eskilarini avtomatik o'chiradi
- Multi-Bot rejimida qaysi bot orqali kelgani ham saqlanadi

---

## 🚀 O'rnatish va Sozlash

### 1. Supabase

1. [supabase.com](https://supabase.com) da yangi loyiha yarating
2. SQL Editor da `supabase_schema.sql` ni ishga tushiring
3. Settings > API dan `URL` va `service_role key` ni oling

### 2. Environment Variables

Vercel Dashboard > Settings > Environment Variables:

```env
# Botlar (vergul bilan ajratilgan, 1 yoki undan ko'p)
BOT_TOKENS=token1,token2,token3

# Yoki faqat bitta bot uchun:
# BOT_TOKEN=your_single_bot_token

# AI API kalitlari (vergul bilan bir nechta bo'lishi mumkin)
GROQ_API_KEY=gsk_key1,gsk_key2
GEMINI_API_KEY=your_gemini_key

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_service_role_key

# Admin
ADMIN_ID=your_telegram_user_id

# O'yinlar
SNAKE_GAME_SHORT_NAME=snake_game_bot
GAME2048_SHORT_NAME=game2048_bot
APP_URL=https://your-app.vercel.app
```

### 3. Deploy to Vercel

```bash
git add .
git commit -m "Deploy"
git push
# Vercel da: New Project > Import from GitHub
```

### 4. Webhook O'rnatish (Avtomatik)

Deploy tugagandan so'ng brauzerda oching:

```
https://your-app.vercel.app/api/setup-webhooks
```

Bu sahifa **barcha botlaringiz** uchun alohida webhook URL'larni avtomatik o'rnatadi. Boshqa hech narsa qilish shart emas!

---

## 📂 Loyiha Strukturasi

```
├── api/index.py               # FastAPI webhook + game routes + setup-webhooks
├── bot/
│   ├── config.py              # Environment config, Multi-Bot token parser
│   ├── database.py            # Supabase REST client + FIFO pruner
│   ├── locales.py             # UZ/RU/EN translations
│   └── main.py                # Multi-Bot manager & Dispatcher
├── handlers/
│   ├── start.py               # /start, /help, /stats, menu
│   ├── converter.py           # File conversion (55+ formats)
│   ├── ai_chat.py             # AI chat + inline video + inline games
│   ├── games.py               # Game callback (Play button)
│   └── font_handler.py        # /font Unicode stilizatsiya
├── converters/
│   ├── registry.py            # Auto-detect & routing
│   ├── images.py              # Pillow conversions
│   ├── documents.py           # DOCX/PDF/TXT/MD/HTML
│   ├── spreadsheets.py        # XLSX/CSV/JSON
│   ├── data_formats.py        # XML/JSON/YAML
│   ├── archives.py            # ZIP/7Z/TAR
│   ├── ebooks.py              # EPUB
│   └── video_converter.py     # Video → GIF/Audio
├── games/
│   ├── snake_html.py          # HTML5 Snake o'yini
│   └── game2048_html.py       # HTML5 2048 o'yini
├── keyboards/
│   ├── main_menu.py           # Reply keyboard
│   └── converter_kb.py        # Inline format buttons
├── utils/
│   ├── file_helper.py         # Download/cleanup helpers
│   ├── link_downloader.py     # yt-dlp video download + web scraper
│   ├── token_rotator.py       # Multi-API key 429 rotation
│   └── font_engine.py         # 12 Unicode font mappings
├── supabase_schema.sql        # Database schema
├── requirements.txt
└── vercel.json
```

## 🤖 Buyruqlar

| Buyruq | Vazifasi |
|---|---|
| `/start` | Botni ishga tushirish, tilni aniqlash |
| `/help` | Barcha formatlar ro'yxati |
| `/clear` | AI suhbat xotirasi (kontekst)ni tozalash |
| `/font` | Unicode font stilizatsiyasi |
| `/stats` | Admin statistikasi (faqat ADMIN_ID) |
| `@botusername` | Inline: o'yinlar (bo'sh), AI javob (matn), video (link) |

## ⚙️ Texnologiyalar

- **Python 3.11+** · **Aiogram 3.x** · **FastAPI**
- **Vercel** (Serverless deployment)
- **Supabase** (PostgreSQL REST API)
- **Groq / Gemini** (AI Chat)
- **yt-dlp** (Video downloader)
- **Pillow, PyMuPDF, openpyxl** (File conversion)
