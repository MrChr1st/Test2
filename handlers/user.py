from typing import Optional

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import Config
from database import Database
from i18n import t
from keyboards import CURRENCIES, confirm_keyboard, currency_keyboard, language_keyboard, main_menu_kb
from services.calculator import calculate_exchange
from services.rates import RateService

router = Router()


class ExchangeFlow(StatesGroup):
    choosing_from = State()
    choosing_to = State()
    entering_amount = State()
    confirming = State()


def get_user_router() -> Router:
    return router


def get_user_language(db: Database, user_id: int) -> str:
    user = db.get_user(user_id)
    if user and user.get("language") in ("ru", "en"):
        return str(user["language"])
    return "ru"


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, db: Database, config: Config) -> None:
    await state.clear()
    referrer_id: Optional[int] = None
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].startswith("ref_"):
            try:
                candidate = int(parts[1].replace("ref_", "").strip())
                if candidate != message.from_user.id:
                    referrer_id = candidate
            except ValueError:
                pass
    language = get_user_language(db, message.from_user.id)
    db.upsert_user(message.from_user.id, message.from_user.username, message.from_user.full_name, language, referrer_id)
    await message.answer(
        t(language, "welcome", name=message.from_user.full_name),
        reply_markup=main_menu_kb(language, is_admin=message.from_user.id in config.admin_ids),
    )


@router.message(F.text.in_({"Обменять", "Exchange"}))
async def exchange_entry(message: Message, state: FSMContext, db: Database) -> None:
    language = get_user_language(db, message.from_user.id)
    await state.clear()
    await state.set_state(ExchangeFlow.choosing_from)
    await message.answer(t(language, "choose_from"), reply_markup=currency_keyboard("from"))


@router.callback_query(F.data.startswith("from:"))
async def choose_from(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    language = get_user_language(db, callback.from_user.id)
    from_currency = callback.data.split(":", 1)[1]
    await state.update_data(from_currency=from_currency)
    await state.set_state(ExchangeFlow.choosing_to)
    await callback.message.edit_text(t(language, "choose_to"), reply_markup=currency_keyboard("to"))
    await callback.answer()


@router.callback_query(F.data.startswith("to:"))
async def choose_to(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    language = get_user_language(db, callback.from_user.id)
    to_currency = callback.data.split(":", 1)[1]
    data = await state.get_data()
    if data.get("from_currency") == to_currency:
        await callback.answer(t(language, "same_currency"), show_alert=True)
        return
    await state.update_data(to_currency=to_currency)
    await state.set_state(ExchangeFlow.entering_amount)
    await callback.message.edit_text(t(language, "enter_amount", currency=data["from_currency"]))
    await callback.answer()


@router.message(ExchangeFlow.entering_amount)
async def amount_input(message: Message, state: FSMContext, db: Database, config: Config, rate_service: RateService) -> None:
    language = get_user_language(db, message.from_user.id)
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer(t(language, "invalid_amount"))
        return
    data = await state.get_data()
    rates = await rate_service.get_all_rates()
    from_rate_usd = rates[data["from_currency"]]
    to_rate_usd = rates[data["to_currency"]]
    result = calculate_exchange(amount, from_rate_usd, to_rate_usd, config.client_bonus)
    market_rate = from_rate_usd / to_rate_usd
    client_rate = market_rate * config.client_bonus
    bonus_percent = (config.client_bonus - 1) * 100
    await state.update_data(amount=amount, result=result, from_rate_usd=from_rate_usd, to_rate_usd=to_rate_usd)
    await state.set_state(ExchangeFlow.confirming)
    await message.answer(
        t(language, "preview", amount=amount, from_currency=data["from_currency"], to_currency=data["to_currency"], result=result, market_rate=market_rate, bonus_percent=bonus_percent, client_rate=client_rate),
        reply_markup=confirm_keyboard(language),
    )


@router.callback_query(F.data == "confirm_exchange")
async def confirm_exchange(callback: CallbackQuery, state: FSMContext, db: Database, config: Config, bot: Bot) -> None:
    language = get_user_language(db, callback.from_user.id)
    data = await state.get_data()
    request_id = db.create_exchange_request(
        callback.from_user.id, callback.from_user.username, callback.from_user.full_name,
        data["from_currency"], data["to_currency"], float(data["amount"]), float(data["result"]),
        float(data["from_rate_usd"]), float(data["to_rate_usd"]), float(config.client_bonus),
    )
    bonus_percent = (config.client_bonus - 1) * 100
    text = t("ru", "new_request_admin", request_id=request_id, full_name=callback.from_user.full_name,
             username=f"@{callback.from_user.username}" if callback.from_user.username else "-",
             user_id=callback.from_user.id, from_currency=data["from_currency"], to_currency=data["to_currency"],
             amount=float(data["amount"]), result=float(data["result"]), bonus_percent=bonus_percent)
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except TelegramForbiddenError:
            pass
        except Exception:
            pass
    await callback.message.edit_text(t(language, "request_saved", request_id=request_id))
    await state.clear()
    await callback.message.answer(
        t(language, "main_menu"),
        reply_markup=main_menu_kb(language, is_admin=callback.from_user.id in config.admin_ids),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_flow")
async def cancel_flow(callback: CallbackQuery, state: FSMContext, db: Database, config: Config) -> None:
    language = get_user_language(db, callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(t(language, "main_menu"))
    await callback.message.answer(t(language, "main_menu"), reply_markup=main_menu_kb(language, is_admin=callback.from_user.id in config.admin_ids))
    await callback.answer()


@router.message(F.text.in_({"Курс валют", "Rates"}))
async def show_rates(message: Message, db: Database, rate_service: RateService, config: Config) -> None:
    language = get_user_language(db, message.from_user.id)
    rates = await rate_service.get_all_rates()
    lines = [f"{c}: {rates[c]:.6f} USD" for c in CURRENCIES]
    lines += ["", f"Client bonus: +{(config.client_bonus - 1) * 100:.2f}%"]
    await message.answer(t(language, "rates_text", rates="\n".join(lines)))


@router.message(F.text.in_({"Реферальная программа", "Referral program"}))
async def show_referral(message: Message, db: Database, config: Config) -> None:
    language = get_user_language(db, message.from_user.id)
    db.upsert_user(message.from_user.id, message.from_user.username, message.from_user.full_name, language)
    count = db.get_referral_count(message.from_user.id)
    link = f"https://t.me/{config.bot_username}?start=ref_{message.from_user.id}"
    bonus_text = config.referral_bonus_text_ru if language == "ru" else config.referral_bonus_text_en
    await message.answer(t(language, "referral_text", link=link, count=count, bonus_text=bonus_text))


@router.message(F.text.in_({"Поддержка", "Support"}))
async def show_support(message: Message, db: Database, config: Config) -> None:
    language = get_user_language(db, message.from_user.id)
    await message.answer(t(language, "support_text", support=config.support_username))


@router.message(F.text.in_({"Смена языка", "Change language"}))
async def language_prompt(message: Message, db: Database) -> None:
    language = get_user_language(db, message.from_user.id)
    await message.answer(t(language, "language_prompt"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery, db: Database, config: Config) -> None:
    language = callback.data.split(":", 1)[1]
    db.upsert_user(callback.from_user.id, callback.from_user.username, callback.from_user.full_name, language)
    db.set_language(callback.from_user.id, language)
    await callback.message.edit_text(t(language, "language_changed_ru" if language == "ru" else "language_changed_en"))
    await callback.message.answer(t(language, "main_menu"), reply_markup=main_menu_kb(language, is_admin=callback.from_user.id in config.admin_ids))
    await callback.answer()
