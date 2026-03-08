КлиентБот -> Supabase shared stats

Не меняя текущую логику обмена, этот патч добавляет параллельную запись событий и заявок в общую Supabase/Postgres БД.

Что заменить:
- handlers/user.py

Что добавить:
- services/supabase_sync.py
- services/reportbot_shared.py
- report_settings.py в корень проекта

Что добавить в requirements.txt:
psycopg2-binary==2.9.9
openpyxl==3.1.5

Что должно быть в .env КлиентБота:
DATABASE_URL=postgresql://...

Что должно быть в report_settings.py:
- токен Repoorrttt_bot
- PRIVATE_CHAT_ID
