import asyncio
import json
import logging
import urllib.error
import urllib.request
from pathlib import Path

from report_settings import REPORT_BOT_TOKEN, REPORT_CHAT_ID


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


async def _send_raw(text: str) -> bool:
    url = f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": str(REPORT_CHAT_ID),
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
    items = _read_queue()
    if not items:
        return True

    remaining = []
    for item in items:
        ok = await _send_raw(item["text"])
        if not ok:
            remaining.append(item)

    _rewrite_queue(remaining)
    return len(remaining) == 0


async def send_report(text: str) -> bool:
    if not REPORT_BOT_TOKEN or not REPORT_CHAT_ID or not text:
        logging.warning("[report_sender] missing token/chat/text")
        return False

    ok = await _send_raw(text)
    if not ok:
        _queue_message(text)
        logging.warning("[report_sender] queued unsent message")

    await flush_report_queue()
    return ok
