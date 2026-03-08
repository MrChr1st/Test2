import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path


QUEUE_FILE = "report_queue.jsonl"


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


def _queue_message(text: str):
    item = {"text": text}
    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _read_queue():
    path = Path(QUEUE_FILE)
    if not path.exists():
        return []

    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def _rewrite_queue(items):
    path = Path(QUEUE_FILE)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


async def _send_raw(bot_token: str, chat_id: str, text: str) -> bool:
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


async def flush_report_queue() -> bool:
    bot_token = os.getenv("REPORT_BOT_TOKEN", "").strip()
    chat_id = os.getenv("REPORT_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        logging.warning("[report_sender] flush skipped: missing env")
        return False

    items = _read_queue()
    if not items:
        return True

    remaining = []
    for item in items:
        ok = await _send_raw(bot_token, chat_id, item["text"])
        if not ok:
            remaining.append(item)

    _rewrite_queue(remaining)
    return len(remaining) == 0


async def send_report(text: str) -> bool:
    bot_token = os.getenv("REPORT_BOT_TOKEN", "").strip()
    chat_id = os.getenv("REPORT_CHAT_ID", "").strip()

    if not bot_token or not chat_id or not text:
        logging.warning(
            f"[report_sender] missing env: token={bool(bot_token)} chat={chat_id!r}"
        )
        return False

    ok = await _send_raw(bot_token, chat_id, text)
    if not ok:
        _queue_message(text)
        logging.warning("[report_sender] queued unsent message")

    await flush_report_queue()
    return ok
