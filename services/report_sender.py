import aiohttp


async def send_report(bot_token: str, chat_id: str, text: str) -> None:
    if not bot_token or not chat_id or not text:
        return

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json=payload, timeout=15)
        except Exception:
            pass