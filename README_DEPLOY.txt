WHAT TO UPLOAD TO GITHUB
- main.py
- config.py
- database.py
- i18n.py
- keyboards.py
- requirements.txt
- .env.example
- .gitignore
- handlers/ folder
- services/ folder

WHAT TO KEEP ONLY IN BOTHOST
- .env  (create from .env.example and put your real BOT_TOKEN)
- exchange_bot.db (will appear automatically after first launch)

HOW TO START ON BOTHOST
1. Upload all project files from this archive to GitHub.
2. Connect the repository in Bothost.
3. In Bothost create the .env file from .env.example.
4. Put your real Telegram token from BotFather in BOT_TOKEN.
5. Put your Telegram numeric ID in ADMIN_IDS.
6. Start the app with command: python main.py

IMPORTANT
- Never commit the real .env file to GitHub.
- If Bothost caches the old broken build, do a full rebuild/redeploy.
