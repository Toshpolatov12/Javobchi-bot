-- ==============================================
-- Supabase SQL: Telegram File Converter Bot
-- ==============================================
-- Bu SQL ni Supabase Dashboard > SQL Editor da ishga tushiring.

-- 1. Users jadvali
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,           -- Telegram user_id
    username TEXT DEFAULT '',         -- @username
    full_name TEXT DEFAULT '',        -- Ism familiya
    language TEXT DEFAULT 'uz',       -- Til: uz yoki ru
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Activities jadvali (fayl faoliyati)
CREATE TABLE IF NOT EXISTS activities (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    file_name TEXT NOT NULL,          -- Fayl nomi
    file_type TEXT NOT NULL,          -- Kirish formati (pdf, docx, jpg...)
    file_size BIGINT DEFAULT 0,       -- Fayl hajmi (bytes)
    action TEXT NOT NULL,             -- Amal (masalan: "pdf→docx")
    target_format TEXT NOT NULL,      -- Chiqish formati
    status TEXT DEFAULT 'pending',    -- success, error, pending
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Chat History jadvali (AI suhbat konteksti va xotirasi)
CREATE TABLE IF NOT EXISTS chat_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    role TEXT NOT NULL,               -- 'user' yoki 'assistant'
    content TEXT NOT NULL,            -- Xabar matni
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Indekslar (tezlik uchun)
CREATE INDEX IF NOT EXISTS idx_activities_user_id ON activities(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- 5. Updated_at avtomatik yangilash
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- 6. RLS (Row Level Security) — API key bilan ishlash uchun
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Service role uchun to'liq ruxsat (bot orqali)
CREATE POLICY "Service role full access on users"
    ON users FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on activities"
    ON activities FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on chat_history"
    ON chat_history FOR ALL
    USING (true)
    WITH CHECK (true);
