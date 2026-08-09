# 🔄 Universal File Converter Bot

Telegram bot for file format conversion — deployed on Vercel, powered by Python + Aiogram 3.

## ✨ Features

- **40+ file conversions** — images, documents, spreadsheets, archives, data formats, e-books
- **AI Chat** — Gemini API powered assistant (text + inline mode)
- **User tracking** — Supabase database for user & activity logging
- **Multi-language** — Uzbek & Russian support
- **Serverless** — Vercel webhook deployment

## 📁 Supported Formats

| Category | Conversions |
|---|---|
| 🖼 Images | PNG ↔ JPG, WEBP, BMP, TIFF, ICO · HEIC → JPG |
| 📄 Documents | DOCX → PDF, TXT, HTML · PDF → TXT, DOCX, PNG · TXT → PDF, DOCX · MD → HTML, PDF · HTML → PDF |
| 📊 Spreadsheets | XLSX ↔ CSV, JSON · XLS → XLSX · CSV ↔ JSON · XLSX → PDF |
| 💾 Data | JSON ↔ XML ↔ YAML |
| 📦 Archives | ZIP ↔ TAR, 7Z · 7Z, TAR, GZ → ZIP |
| 📚 E-books | EPUB → TXT, PDF |

## 🚀 Setup

### 1. Supabase

1. [supabase.com](https://supabase.com) da yangi loyiha yarating
2. SQL Editor da `supabase_schema.sql` ni ishga tushiring
3. Settings > API dan `URL` va `service_role key` ni oling

### 2. Environment Variables

Vercel Dashboard > Settings > Environment Variables:

```
BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_service_role_key
ADMIN_ID=your_telegram_user_id
```

### 3. Deploy to Vercel

```bash
# GitHub ga push qiling
git add .
git commit -m "File Converter Bot"
git push

# Vercel da import qiling
# vercel.com > New Project > Import from GitHub
```

### 4. Set Webhook

Deploy tugagandan so'ng:

```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-app.vercel.app/api/webhook
```

## 📂 Project Structure

```
├── api/index.py           # FastAPI webhook handler
├── bot/
│   ├── config.py          # Environment config
│   ├── database.py        # Supabase REST client
│   ├── locales.py         # UZ/RU translations
│   └── main.py            # Bot & Dispatcher
├── handlers/
│   ├── start.py           # /start, /help, /stats, menu
│   ├── converter.py       # File conversion logic
│   └── ai_chat.py         # Gemini AI + inline mode
├── converters/
│   ├── registry.py        # Auto-detect & routing
│   ├── images.py          # Pillow conversions
│   ├── documents.py       # DOCX/PDF/TXT/MD/HTML
│   ├── spreadsheets.py    # XLSX/CSV/JSON
│   ├── data_formats.py    # XML/JSON/YAML
│   ├── archives.py        # ZIP/7Z/TAR
│   └── ebooks.py          # EPUB
├── keyboards/
│   ├── main_menu.py       # Reply keyboard
│   └── converter_kb.py    # Inline format buttons
├── utils/
│   └── file_helper.py     # Download/cleanup helpers
├── supabase_schema.sql    # Database schema
├── requirements.txt
└── vercel.json
```

## 🤖 Admin Commands

- `/stats` — Foydalanuvchilar soni va oxirgi faollik (faqat ADMIN_ID uchun)
