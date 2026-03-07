from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import Database
from i18n import t
from keyboards import admin_request_keyboard, language_keyboard, main_menu
from services.calculator import CalculatorService
from services.rates import RateService

SUPPORTED_CURRENCIES = {"BTC", "USDT", "TON", "USD", "EUR", "RUB", "INR"}


class RequestStates(StatesGroup):
    waiting_for_pair = State()
    waiting_for_amount = State()



def get_user_router(
    db: Database,
    rate_service: RateService,
    calculator: CalculatorService,
    admin_ids: list[int],
) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start_handler(message: Message):
        db.add_user(message.from_user.id, message.from_user.username)
        lang = db.get_user_language(message.from_user.id)
        await message.answer(t(lang, "choose_lang"), reply_markup=language_keyboard())
        await message.answer(t(lang, "start"), reply_markup=main_menu(lang))

    @router.callback_query(F.data.startswith("lang:"))
    async def language_handler(callback: CallbackQuery):
        lang = callback.data.split(":", 1)[1]
        if lang not in {"ru", "en"}:
            await callback.answer("Unknown language", show_alert=True)
            return
        db.add_user(callback.from_user.id, callback.from_user.username, lang)
        db.set_user_language(callback.from_user.id, lang)
        await callback.message.answer(t(lang, "language_saved"), reply_markup=main_menu(lang))
        await callback.answer()

    @router.message(F.text.in_({"Новая заявка", "New request"}))
    async def new_request_handler(message: Message, state: FSMContext):
        lang = db.get_user_language(message.from_user.id)
        await state.clear()
        await state.set_state(RequestStates.waiting_for_pair)
        await message.answer(t(lang, "enter_pair"))

    @router.message(RequestStates.waiting_for_pair)
    async def pair_handler(message: Message, state: FSMContext):
        lang = db.get_user_language(message.from_user.id)
        text = (message.text or "").strip().upper().replace("/", " ").replace("-", " ")
        parts = [part for part in text.split() if part]

        if len(parts) != 2 or parts[0] == parts[1]:
            await message.answer(t(lang, "invalid_pair"))
            return

        source_currency, target_currency = parts
        if source_currency not in SUPPORTED_CURRENCIES or target_currency not in SUPPORTED_CURRENCIES:
            await message.answer(t(lang, "invalid_pair"))
            return

        await state.update_data(source_currency=source_currency, target_currency=target_currency)
        await state.set_state(RequestStates.waiting_for_amount)
        await message.answer(t(lang, "enter_amount"))

    @router.message(RequestStates.waiting_for_amount)
    async def amount_handler(message: Message, state: FSMContext):
        lang = db.get_user_language(message.from_user.id)
        raw = (message.text or "").strip().replace(",", ".")

        try:
            amount = float(raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await message.answer(t(lang, "invalid_amount"))
            return

        data = await state.get_data()
        source_currency = data["source_currency"]
        target_currency = data["target_currency"]
        rates = await rate_service.get_all_rates()
        calc = calculator.calculate(amount, source_currency, target_currency, rates)

        request_id = db.create_request(
            user_id=message.from_user.id,
            username=message.from_user.username,
            source_currency=source_currency,
            target_currency=target_currency,
            amount=amount,
            base_rate=calc["base_rate"],
            final_rate=calc["final_rate"],
            receive_amount=calc["receive_amount"],
        )

        lines = [
            f"{t(lang, 'request_created')} #{request_id}",
            f"{source_currency} -> {target_currency}",
            f"Amount: {amount:.8f}",
            f"Base rate: {calc['base_rate']:.8f}",
            f"Final rate: {calc['final_rate']:.8f}",
            f"Receive: {calc['receive_amount']:.8f}",
        ]
        await message.answer("\n".join(lines), reply_markup=main_menu(lang))

        admin_lines = [
            f"New request #{request_id}",
            f"User: @{message.from_user.username or '-'} ({message.from_user.id})",
            f"Pair: {source_currency} -> {target_currency}",
            f"Amount: {amount:.8f}",
            f"Base rate: {calc['base_rate']:.8f}",
            f"Final rate: {calc['final_rate']:.8f}",
            f"Receive: {calc['receive_amount']:.8f}",
        ]
        for admin_id in admin_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    "\n".join(admin_lines),
                    reply_markup=admin_request_keyboard(request_id),
                )
            except Exception:
                pass

        await state.clear()

    @router.message(F.text.in_({"Курсы", "Rates"}))
    async def rates_handler(message: Message):
        lang = db.get_user_language(message.from_user.id)
        rates = await rate_service.get_all_rates()
        lines = [t(lang, "current_rates")]
        for code, value in rates.items():
            lines.append(f"{code}: {value:.8f}")
        await message.answer("\n".join(lines), reply_markup=main_menu(lang))

    @router.message(F.text.in_({"Назад", "Back"}))
    async def back_handler(message: Message, state: FSMContext):
        lang = db.get_user_language(message.from_user.id)
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=main_menu(lang))

    return router
