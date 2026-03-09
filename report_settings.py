import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv()

REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "").strip()
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "").strip()
PRIVATE_CHAT_ID = os.getenv("PRIVATE_CHAT_ID", "").strip()
AUTO_REPORT_HOURS = int(os.getenv("AUTO_REPORT_HOURS", "24").strip())
