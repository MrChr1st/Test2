import json
import logging
import urllib.request
import urllib.error


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


async def send_report(bot_token: str, chat_id: str, text: str):
    if not bot_token or not chat_id or not text:
        logging.warning("[report_sender] missing bot_token/chat_id/text")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "disable_web_page_preview": True,
    }

    try:
        status, body = _post_json(url, payload, timeout=15)
        logging.warning(f"[report_sender] status={status} body={body}")

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = str(e)

        logging.exception(
            f"[report_sender] HTTPError status={e.code} body={body}"
        )

    except Exception as e:
        logging.exception(
            f"[report_sender] failed: {e}"
        )