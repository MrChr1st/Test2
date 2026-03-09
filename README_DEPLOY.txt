Функции в этой сборке:
- 💱 обмен валют
- 📊 живой курс
- 🎁 реферальная программа
- 💳 карта / 🪙 крипта / ⚡ СБП
- 📋 кнопки скопировать карту и BYBIT ID
- 📷 кнопка получить QR код
- 👨‍💼 админ панель и команды
- 📩 уведомления оператору
- нижние кнопки для всех этапов выбора
- /done REQUEST_ID для учета рефералки по завершенным заявкам

Перед запуском:
1. Заполни ENV.
2. Админом открой бота и нажми /start.
3. Запуск: python main.py

Crypto payment options now include BYBIT ID, USDT (TRC20), TON, and BTC copy buttons.

CHANNEL_TARGET: invite link alone is not enough. Add the bot to the channel as admin and set CHANNEL_TARGET to @channelusername or numeric chat id.


Важно для этой сборки:
- основная БД только Supabase/Postgres через DATABASE_URL
- SQLite больше не используется
- данные КлиентБота пишутся прямо в shared_users, shared_exchange_requests, shared_exchange_events


BOT_USERNAME for this client bot: Ccchangerrr_bot
