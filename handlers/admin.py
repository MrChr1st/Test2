from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import Config
from database import Database
from i18n import t
from keyboards import admin_keyboard, main_menu_kb

router = Router()

def get_admin_router() -> Router:
    return router

def get_lang(db: Database, user_id: int) -> str:
    user = db.get_user(user_id)
    if user and user.get("language") in ("ru", "en"):
        return str(user["language"])
    return "ru"

def is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admin_ids

@router.message(Command("admin"))
@router.message(F.text.in_({"Админ-панель", "Admin panel"}))
async def admin_panel(message: Message, db: Database, config: Config) -> None:
    language = get_lang(db, message.from_user.id)
    if not is_admin(message.from_user.id, config):
        await message.answer(t(language, "access_denied"))
        return
    await message.answer(t(language, "admin_panel"), reply_markup=admin_keyboard(language))

@router.message(Command("admin_stats"))
async def admin_stats(message: Message, db: Database, config: Config) -> None:
    language = get_lang(db, message.from_user.id)
    if not is_admin(message.from_user.id, config):
        await message.answer(t(language, "access_denied"))
        return
    await message.answer(t(language, "admin_stats", users=db.get_total_users(), requests_total=db.get_total_requests(), requests_today=db.get_requests_today()))

@router.message(Command("admin_requests"))
async def admin_requests(message: Message, db: Database, config: Config) -> None:
    language = get_lang(db, message.from_user.id)
    if not is_admin(message.from_user.id, config):
        await message.answer(t(language, "access_denied"))
        return
    items = db.get_last_requests(10)
    if not items:
        await message.answer(t(language, "no_requests"))
        return
    lines = [t(language, "admin_last_requests_title"), ""]
    for item in items:
        lines.append(f"#{item['id']} | {item['from_currency']} → {item['to_currency']} | {item['amount']:.6f} -> {item['result_amount']:.6f} | user {item['user_id']}")
    await message.answer("\n".join(lines))

@router.message(F.text.in_({"В меню", "To menu"}))
async def back_to_menu(message: Message, db: Database, config: Config) -> None:
    language = get_lang(db, message.from_user.id)
    await message.answer(t(language, "main_menu"), reply_markup=main_menu_kb(language, is_admin=is_admin(message.from_user.id, config)))
