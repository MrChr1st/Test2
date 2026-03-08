from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from keyboards import (
    CURRENCIES,
    QUOTE_CURRENCIES,
    admin_menu_kb,
    back_kb,
    card_action_kb,
    card_submethod_kb,
    card_submethod_with_back_kb,
    crypto_choice_kb,
    crypto_choice_with_back_kb,
    crypto_selected_action_kb,
    currency_kb,
    language_kb,
    main_menu_kb,
    paid_kb,
    payment_method_kb,
    payment_method_with_back_kb,
    quote_currency_kb,
    remove_kb,
)
from services.calculator import calculate_fee_with_referral_discount
from services.report_sender import send_report
from texts import TEXTS

router = Router()


class ExchangeForm(StatesGroup):
    from_currency = State()
    to_currency = State()
    amount = State()
    receive_details = State()
    payment_method = State()
    crypto_method = State()


class RatesForm(StatesGroup):
    quote = State()


def get_lang(db, user_id: int) -> str:
    return db.get_language(user_id)


def t(lang: str, key: str, **kwargs) -> str:
    return TEXTS[lang][key].format(**kwargs)


def is_admin(user_id: int, config) -> bool:
    return user_id in config.admin_ids


def user_display(username: str | None, user_id: int) -> str:
    return f"@{username}" if username else f"id={user_id}"


def user_profile_link(user_id: int) -> str:
    return f"tg://user?id={user_id}"


async def send_admin_targets(bot, config, text: str):
    await send_report(text)


def is_back(text: str) -> bool:
    return text in ["⬅️ Назад", "⬅️ Back"]


async def ensure_not_blocked(message: Message, db) -> bool:
    if db.is_user_blocked(message.from_user.id):
        await message.answer(TEXTS[get_lang(db, message.from_user.id)]["blocked"])
        return False
    return True


def payment_method_name(lang: str, method: str) -> str:
    names = {
        "ru": {"sbp": "СБП", "card": "Карта", "crypto": "Крипта"},
        "en": {"sbp": "SBP", "card": "Card", "crypto": "Crypto"},
    }
    return names[lang][method]


def payment_sub_name(lang: str, submethod: str) -> str:
    names = {
        "ru": {"-": "-", "card_number": "Номер карты", "tg_wallet": "Telegram Wallet", "bybit": "BYBIT ID", "usdt": "USDT (TRC20)", "ton": "TON", "btc": "BTC"},
        "en": {"-": "-", "card_number": "Card number", "tg_wallet": "Telegram Wallet", "bybit": "BYBIT ID", "usdt": "USDT (TRC20)", "ton": "TON", "btc": "BTC"},
    }
    return names[lang][submethod]


@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, db, config):
    referred_by = None
    if command.args and command.args.startswith("ref_"):
        code = command.args.replace("ref_", "", 1).strip()
        ref_user_id = db.get_user_id_by_ref_code(code)
        if ref_user_id and ref_user_id != message.from_user.id:
            referred_by = ref_user_id
    db.create_user_if_not_exists(message.from_user.id, message.from_user.username, "ru", referred_by)
    if db.is_user_blocked(message.from_user.id):
        await message.answer(TEXTS["ru"]["blocked"])
        return
    await message.answer(TEXTS["ru"]["choose_language"], reply_markup=language_kb())


@router.message(F.text == "🇷🇺 Русский")
async def set_ru(message: Message, db, config):
    db.set_language(message.from_user.id, "ru")
    await message.answer(TEXTS["ru"]["language_selected"], reply_markup=main_menu_kb("ru", is_admin(message.from_user.id, config)))


@router.message(F.text == "🇬🇧 English")
async def set_en(message: Message, db, config):
    db.set_language(message.from_user.id, "en")
    await message.answer(TEXTS["ru"]["language_selected_en"], reply_markup=main_menu_kb("en", is_admin(message.from_user.id, config)))


@router.message(F.text.in_(["🌍 Смена языка", "🌍 Change language"]))
async def change_lang(message: Message):
    await message.answer(TEXTS["ru"]["choose_language"], reply_markup=language_kb())


@router.message(F.text.in_(["👨‍💼 Admin"]))
async def admin_menu(message: Message, db, config):
    if not is_admin(message.from_user.id, config):
        return
    lang = get_lang(db, message.from_user.id)
    await message.answer(TEXTS[lang]["admin_help"], parse_mode="Markdown", reply_markup=admin_menu_kb(lang))


@router.message(F.text.in_(["📚 Заявки", "📚 Requests"]))
async def admin_requests_button(message: Message):
    await message.answer("/requests")


@router.message(F.text.in_(["ℹ️ Помощь админу", "ℹ️ Admin help"]))
async def admin_help_button(message: Message, db):
    lang = get_lang(db, message.from_user.id)
    await message.answer(TEXTS[lang]["admin_help"], parse_mode="Markdown")


@router.message(F.text.in_(["🛟 Поддержка", "🛟 Support"]))
async def support(message: Message, db, config):
    if not await ensure_not_blocked(message, db):
        return
    lang = get_lang(db, message.from_user.id)
    await message.answer(
        t(lang, "support", support=config.support_username),
        reply_markup=main_menu_kb(lang, is_admin(message.from_user.id, config)),
    )


@router.message(F.text.in_(["🎁 Реферальная программа", "🎁 Referral program"]))
async def referral(message: Message, db, config):
    if not await ensure_not_blocked(message, db):
        return
    lang = get_lang(db, message.from_user.id)
    code = db.get_user_ref_code(message.from_user.id)
    if not code:
        db.create_user_if_not_exists(message.from_user.id, message.from_user.username, lang)
        code = db.get_user_ref_code(message.from_user.id)

    invited = db.get_referrals_count(message.from_user.id)
    completed = db.count_completed_referral_requests(message.from_user.id)
    discount = min(invited * config.referral_fee_discount_per_user, config.max_referral_fee_discount)
    current_fee = max(config.fee - discount, 0.0)
    link = f"https://t.me/{config.bot_username}?start=ref_{code}"

    await message.answer(
        t(
            lang,
            "referral",
            code=code,
            link=link,
            invited=invited,
            completed=completed,
            base_fee=config.fee * 100,
            discount=discount * 100,
            current_fee=current_fee * 100,
        ),
        parse_mode="Markdown",
        reply_markup=main_menu_kb(lang, is_admin(message.from_user.id, config)),
    )


@router.message(F.text.in_(["📊 Курс валют", "📊 Rates"]))
async def rates_start(message: Message, db, state: FSMContext):
    if not await ensure_not_blocked(message, db):
        return
    lang = get_lang(db, message.from_user.id)
    await state.clear()
    await state.set_state(RatesForm.quote)
    await message.answer(TEXTS[lang]["rates_intro"], reply_markup=quote_currency_kb())


@router.message(RatesForm.quote)
async def rates_pick(message: Message, db, rate_service, state: FSMContext, config):
    lang = get_lang(db, message.from_user.id)
    quote = (message.text or "").strip().upper()
    if quote not in QUOTE_CURRENCIES:
        await message.answer(TEXTS[lang]["invalid_currency"], reply_markup=quote_currency_kb())
        return
    table = await rate_service.get_table(quote)
    body = "\n".join(f"• 1 {cur} = `{val}` {quote}" for cur, val in table.items() if cur != quote)
    await state.clear()
    await message.answer(
        t(lang, "rates_fmt", quote=quote, body=body),
        parse_mode="Markdown",
        reply_markup=main_menu_kb(lang, is_admin(message.from_user.id, config)),
    )


@router.message(F.text.in_(["💱 Обменять", "💱 Exchange"]))
async def exchange_start(message: Message, db, state: FSMContext):
    if not await ensure_not_blocked(message, db):
        return
    lang = get_lang(db, message.from_user.id)
    await state.clear()
    await state.set_state(ExchangeForm.from_currency)
    await message.answer(TEXTS[lang]["exchange_intro"], reply_markup=currency_kb())


@router.message(ExchangeForm.from_currency)
async def exchange_from(message: Message, db, state: FSMContext):
    lang = get_lang(db, message.from_user.id)
    raw_text = (message.text or "").strip()
    if is_back(raw_text):
        await state.set_state(ExchangeForm.from_currency)
        await message.answer(TEXTS[lang]["exchange_intro"], reply_markup=currency_kb())
        return
    cur = raw_text.upper()
    if cur not in CURRENCIES:
        await message.answer(TEXTS[lang]["invalid_currency"], reply_markup=currency_kb())
        return
    await state.update_data(from_currency=cur)
    await state.set_state(ExchangeForm.to_currency)
    await message.answer(TEXTS[lang]["choose_to"], reply_markup=currency_kb(exclude=cur))


@router.message(ExchangeForm.to_currency)
async def exchange_to(message: Message, db, state: FSMContext):
    lang = get_lang(db, message.from_user.id)
    raw_text = (message.text or "").strip()
    if is_back(raw_text):
        await state.set_state(ExchangeForm.from_currency)
        await message.answer(TEXTS[lang]["exchange_intro"], reply_markup=currency_kb())
        return
    cur = raw_text.upper()
    data = await state.get_data()
    if cur not in CURRENCIES:
        await message.answer(TEXTS[lang]["invalid_currency"], reply_markup=currency_kb(exclude=data.get("from_currency")))
        return
    if cur == data.get("from_currency"):
        await message.answer(TEXTS[lang]["same_currency"], reply_markup=currency_kb(exclude=data.get("from_currency")))
        return
    await state.update_data(to_currency=cur)
    await state.set_state(ExchangeForm.amount)
    await message.answer(TEXTS[lang]["enter_amount"], reply_markup=back_kb(lang))


@router.message(ExchangeForm.amount)
async def exchange_amount(message: Message, db, config, rate_service, state: FSMContext):
    lang = get_lang(db, message.from_user.id)
    raw_text = (message.text or "").strip()
    if is_back(raw_text):
        data = await state.get_data()
        await state.set_state(ExchangeForm.to_currency)
        await message.answer(TEXTS[lang]["choose_to"], reply_markup=currency_kb(exclude=data.get("from_currency")))
        return
    raw = raw_text.replace(",", ".").strip()
    try:
        amount = float(raw)
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer(TEXTS[lang]["invalid_amount"], reply_markup=back_kb(lang))
        return

    data = await state.get_data()
    fee_fraction = calculate_fee_with_referral_discount(
        config.fee,
        db.get_referrals_count(message.from_user.id),
        config.referral_fee_discount_per_user,
        config.max_referral_fee_discount,
    )
    result_amount, market_rate = await rate_service.convert(amount, data["from_currency"], data["to_currency"], fee_fraction)

    await state.update_data(
        amount_from=amount,
        amount_to=result_amount,
        market_rate=market_rate,
        fee_fraction=fee_fraction,
    )
    await state.set_state(ExchangeForm.receive_details)

    await message.answer(
        t(
            lang,
            "summary",
            amount_from=amount,
            amount_to=result_amount,
            from_cur=data["from_currency"],
            to_cur=data["to_currency"],
            market_rate=market_rate,
            fee=fee_fraction * 100,
        ),
        parse_mode="Markdown",
        reply_markup=remove_kb(),
    )
    if "RUB" in {data["from_currency"], data["to_currency"]}:
        await message.answer(t(lang, "rub_notice", support=config.support_username), parse_mode="Markdown")
    await message.answer(TEXTS[lang]["enter_receive"], reply_markup=back_kb(lang))


@router.message(ExchangeForm.receive_details)
async def exchange_receive(message: Message, db, state: FSMContext):
    lang = get_lang(db, message.from_user.id)
    raw_text = (message.text or "").strip()
    if is_back(raw_text):
        await state.set_state(ExchangeForm.amount)
        await message.answer(TEXTS[lang]["enter_amount"], reply_markup=back_kb(lang))
        return
    await state.update_data(receive_details=raw_text)
    await state.set_state(ExchangeForm.payment_method)
    await message.answer(TEXTS[lang]["choose_payment"], reply_markup=payment_method_with_back_kb(lang))


@router.message(ExchangeForm.payment_method)
async def exchange_payment(message: Message, db, config, state: FSMContext, bot):
    lang = get_lang(db, message.from_user.id)
    text = (message.text or "").strip()
    if is_back(text):
        await state.set_state(ExchangeForm.receive_details)
        await message.answer(TEXTS[lang]["enter_receive"], reply_markup=back_kb(lang))
        return

    if text in ["🪙 Крипта", "🪙 Crypto"]:
        await state.set_state(ExchangeForm.crypto_method)
        await message.answer(TEXTS[lang]["choose_crypto_method"], reply_markup=crypto_choice_with_back_kb(lang))
        return
    if text in ["⚡ СБП", "⚡ SBP"]:
        await _finalize_request(message, state, db, config, lang, "sbp", "-", bot)
        return
    if text in ["💳 Карта", "💳 Card"]:
        await message.answer(TEXTS[lang]["choose_card_submethod"], reply_markup=card_submethod_with_back_kb(lang))
        return
    if text in ["💳 Номер карты", "💳 Card number"]:
        await _finalize_request(message, state, db, config, lang, "card", "card_number", bot)
        return
    if text == "💬 Telegram Wallet":
        await _finalize_request(message, state, db, config, lang, "card", "tg_wallet", bot)
        return

    await message.answer(TEXTS[lang]["choose_payment"], reply_markup=payment_method_with_back_kb(lang))


async def _finalize_request(message, state, db, config, lang, method, submethod, bot):
    data = await state.get_data()
    request_id = db.create_exchange_request(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        from_currency=data["from_currency"],
        to_currency=data["to_currency"],
        amount_from=data["amount_from"],
        amount_to=data["amount_to"],
        receive_details=data["receive_details"],
        payment_method=payment_method_name(lang, method),
        payment_submethod=payment_sub_name(lang, submethod),
        status="waiting_payment" if submethod != "tg_wallet" else "wallet_operator",
    )
    await state.clear()

    created_text = (
        f"🆕 Новая заявка\n\n"
        f"Заявка: #{request_id}\n"
        f"Пользователь: {user_display(message.from_user.username, message.from_user.id)}\n"
        f"ID: {message.from_user.id}\n"
        f"Профиль: {user_profile_link(message.from_user.id)}\n\n"
        f"Обмен: {data['from_currency']} -> {data['to_currency']}\n"
        f"Сумма: {data['amount_from']} {data['from_currency']} -> {data['amount_to']} {data['to_currency']}\n"
        f"Реквизиты: {data['receive_details']}\n"
        f"Оплата: {payment_method_name(lang, method)} / {payment_sub_name(lang, submethod)}"
    )
    await send_admin_targets(bot, config, created_text)

    if method == "card" and submethod == "tg_wallet":
        row = db.get_request_by_id(request_id)
        admin_text = (
            f"🚨 Wallet заявка\n\n"
            f"Заявка: #{row['id']}\n"
            f"Пользователь: {user_display(row['username'], row['user_id'])}\n"
            f"ID: {row['user_id']}\n"
            f"Профиль: {user_profile_link(row['user_id'])}\n\n"
            f"Обмен: {row['from_currency']} -> {row['to_currency']}\n"
            f"Сумма: {row['amount_from']} {row['from_currency']} -> {row['amount_to']} {row['to_currency']}\n"
            f"Реквизиты: {row['receive_details']}\n\n"
            f"Клиент ждёт перевод через Telegram Wallet."
        )
        await send_admin_targets(bot, config, admin_text)
        await message.answer(t(lang, "wallet_operator_msg", support=config.support_username), reply_markup=main_menu_kb(lang, is_admin(message.from_user.id, config)))
        return request_id

    if method == "card" and submethod == "card_number":
        await message.answer(
            t(lang, "card_number_payment", card_number=config.card_number),
            parse_mode="Markdown",
            reply_markup=paid_kb(lang),
        )
        await message.answer(
            t(lang, "copy_card_reply", card_number=config.card_number),
            parse_mode="Markdown",
            reply_markup=card_action_kb(lang),
        )
        return request_id

    if method == "crypto":
        crypto_key = {
            "bybit": "crypto_bybit",
            "usdt": "crypto_usdt",
            "ton": "crypto_ton",
            "btc": "crypto_btc",
        }[submethod]
        await message.answer(
            t(lang, crypto_key, bybit_id=config.bybit_id),
            parse_mode="Markdown",
            reply_markup=paid_kb(lang),
        )
        await message.answer(
            ("Выберите действие:" if lang == "ru" else "Choose an action:"),
            reply_markup=crypto_selected_action_kb(lang, submethod),
        )
        return request_id

    await message.answer(
        t(lang, "request_created_sbp", request_id=request_id, payment_method=payment_method_name(lang, method), payment_url=config.sbp_payment_url),
        parse_mode="Markdown",
        reply_markup=paid_kb(lang),
    )
    return request_id


@router.message(ExchangeForm.crypto_method)
async def exchange_crypto_method(message: Message, db, config, state: FSMContext, bot):
    lang = get_lang(db, message.from_user.id)
    text = (message.text or "").strip()
    if is_back(text):
        await state.set_state(ExchangeForm.payment_method)
        await message.answer(TEXTS[lang]["choose_payment"], reply_markup=payment_method_with_back_kb(lang))
        return
    mapping = {
        "BYBIT ID": "bybit",
        "USDT (TRC20)": "usdt",
        "TON": "ton",
        "BTC": "btc",
    }
    asset = mapping.get(text)
    if not asset:
        await message.answer(TEXTS[lang]["crypto_invalid_choice"], reply_markup=crypto_choice_with_back_kb(lang))
        return
    await _finalize_request(message, state, db, config, lang, "crypto", asset, bot)
    return


@router.callback_query(F.data == "copy_card")
async def copy_card(callback: CallbackQuery, db, config):
    lang = get_lang(db, callback.from_user.id)
    await callback.message.answer(t(lang, "copy_card_reply", card_number=config.card_number), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("copy_crypto:"))
async def copy_crypto(callback: CallbackQuery, db, config):
    lang = get_lang(db, callback.from_user.id)
    asset = callback.data.split(":", 1)[1]
    if asset == "bybit":
        text = t(lang, "copy_bybit_reply", bybit_id=config.bybit_id)
    elif asset == "usdt":
        text = TEXTS[lang]["copy_usdt_reply"]
    elif asset == "ton":
        text = TEXTS[lang]["copy_ton_reply"]
    else:
        text = TEXTS[lang]["copy_btc_reply"]
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("request_qr:"))
async def request_qr(callback: CallbackQuery, db, config, bot):
    lang = get_lang(db, callback.from_user.id)
    asset = callback.data.split(":", 1)[1]
    row = db.get_active_request(callback.from_user.id)
    if row:
        target_value = (
            config.bybit_id if asset == "bybit"
            else ("TCj4c7BQTEWwZtRRqkoKB2fPvZfchBwM1o" if asset == "usdt"
                  else ("UQCsvhcOlwepsTTWqaj3HNyTCU5C38u4Hrf6U2YGjsNoUBW-" if asset == "ton"
                        else "bc1qy6ej90jpr6x086kn4j84m90x7lsu2a99qzz7hf"))
        )
        asset_name = {"bybit": "BYBIT ID", "usdt": "USDT (TRC20)", "ton": "TON", "btc": "BTC"}[asset]
        admin_text = (
            f"📷 Запрос QR-кода\n\n"
            f"Заявка: #{row['id']}\n"
            f"Пользователь: {user_display(row['username'], row['user_id'])}\n"
            f"ID: {row['user_id']}\n"
            f"Профиль: {user_profile_link(row['user_id'])}\n\n"
            f"Метод: {asset_name}: {target_value}"
        )
        await send_admin_targets(bot, config, admin_text)
    await callback.message.answer(TEXTS[lang]["qr_requested_user"])
    await callback.answer()


@router.message(F.text.in_(["✅ Я оплатил", "✅ I paid"]))
async def mark_paid(message: Message, db, config, bot):
    lang = get_lang(db, message.from_user.id)
    row = db.get_active_request(message.from_user.id)
    if not row or row["status"] != "waiting_payment":
        await message.answer(TEXTS[lang]["no_active_request"], reply_markup=main_menu_kb(lang, is_admin(message.from_user.id, config)))
        return

    db.update_request_status(row["id"], "paid_pending_review")
    await message.answer(
        t(lang, "paid_thanks", support=config.support_username),
        reply_markup=main_menu_kb(lang, is_admin(message.from_user.id, config)),
    )

    admin_text = (
        f"💰 Клиент отметил оплату\n\n"
        f"Заявка: #{row['id']}\n"
        f"Пользователь: {user_display(row['username'], row['user_id'])}\n"
        f"ID: {row['user_id']}\n"
        f"Профиль: {user_profile_link(row['user_id'])}\n\n"
        f"Обмен: {row['from_currency']} -> {row['to_currency']}\n"
        f"Сумма: {row['amount_from']} {row['from_currency']} -> {row['amount_to']} {row['to_currency']}\n"
        f"Реквизиты: {row['receive_details']}\n"
        f"Оплата: {row['payment_method']} / {row['payment_submethod'] or '-'}"
    )
    await send_admin_targets(bot, config, admin_text)
