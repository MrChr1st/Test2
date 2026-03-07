from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from texts import TEXTS

router = Router()


def _is_admin(user_id: int, config) -> bool:
    return user_id in config.admin_ids


@router.message(Command("requests"))
async def requests_handler(message: Message, db, config):
    if not _is_admin(message.from_user.id, config):
        return
    lang = "ru"
    rows = db.get_last_requests(limit=100)
    if not rows:
        await message.answer(TEXTS[lang]["requests_empty"])
        return

    current = TEXTS[lang]["requests_header"]
    for row in rows:
        part = TEXTS[lang]["request_row"].format(
            id=row["id"],
            username=row["username"] or "no_username",
            from_cur=row["from_currency"],
            to_cur=row["to_currency"],
            amount_from=row["amount_from"],
            amount_to=row["amount_to"],
            status=row["status"],
            payment_method=row["payment_method"] or "-",
            payment_submethod=row["payment_submethod"] or "-",
        )
        if len(current) + len(part) > 3500:
            await message.answer(current, parse_mode="Markdown")
            current = part
        else:
            current += "\n" + part
    if current:
        await message.answer(current, parse_mode="Markdown")


@router.message(Command("block"))
async def block_handler(message: Message, db, config):
    if not _is_admin(message.from_user.id, config):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Usage: /block USER_ID")
        return
    user_id = int(parts[1].strip())
    db.set_user_blocked(user_id, True)
    await message.answer(TEXTS["ru"]["admin_blocked"])


@router.message(Command("unblock"))
async def unblock_handler(message: Message, db, config):
    if not _is_admin(message.from_user.id, config):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Usage: /unblock USER_ID")
        return
    user_id = int(parts[1].strip())
    db.set_user_blocked(user_id, False)
    await message.answer(TEXTS["ru"]["admin_unblocked"])
