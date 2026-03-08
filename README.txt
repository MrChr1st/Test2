КлиентБот: статистика и автоотчёты теперь считаются в КлиентБоте.
Заменить:
- handlers/user.py
Добавить:
- services/report_stats.py
- report_settings.py в корень проекта
И добавить в requirements.txt строку: openpyxl==3.1.5
Важно: в report_settings.py вставить реальный токен Repoorrttt_bot и свой PRIVATE_CHAT_ID.
Что будет:
- сбор статистики по открытиям обмена, заявкам, оплатам, QR и wallet
- Excel за 24ч
- текстовая финсводка за 24ч
- автоотправка каждые 24ч в личку через Repoorrttt_bot
