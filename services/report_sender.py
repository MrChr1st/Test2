import asyncio
import json
import logging
import os
import urllib.error
import urllib.request


def _post_json(url: str, payload: dict, timeout: int = 15):
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


async def send_report(text: str):
    bot_token = os.getenv("REPORT_BOT_TOKEN", "").strip()
    chat_id = os.getenv("REPORT_CHAT_ID", "").strip()

    if not bot_token or not chat_id or not text:
        logging.warning(
            f"[report_sender] missing env: token={bool(bot_token)} chat={chat_id!r}"
        )
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "disable_web_page_preview": True,
    }

    for attempt in range(1, 4):
        try:
            status, body = await asyncio.to_thread(_post_json, url, payload, 15)
            logging.warning(
                f"[report_sender] attempt={attempt} status={status} body={body}"
            )
            return True

        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = str(e)

            logging.exception(
                f"[report_sender] HTTPError attempt={attempt} status={e.code} body={body}"
            )

        except Exception as e:
            logging.exception(f"[report_sender] failed attempt={attempt}: {e}")

        await asyncio.sleep(1)

    return False