from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from keyboards import (
    CURRENCIES,
    QUOTE_CURRENCIES,
    card_submethod_kb,
    currency_kb,
    language_kb,
    main_menu_kb,
    paid_kb,
    payment_method_kb,
    quote_currency_kb,
    remove_kb,
)
from services.calculator import calculate_fee_with_referral_discount
from texts import TEXTS

router = Router()

class ExchangeForm(StatesGroup):
    from_currency = State()
    to_currency = State()
    amount = State()
    receive_details = State()
    payment_method = State()

class RatesForm(StatesGroup):
    quote = State()

def get_lang(db, user_id: int) -> str:
    return db.get_language(user_id)

def t(lang: str, key: str, **kwargs) -> str:
    return TEXTS[lang][key].format(**kwargs)

def user_display(username: str | None, user_id: int) -> str:
    return f"@{username}" if username else f"id={user_id}"

def user_profile_link(user_id: int) -> str:
    return f"tg://user?id={user_id}"

async def ensure_not_blocked(message: Message, db) -> bool:
    if db.is_user_blocked(message.from_user.id):
        await message.answer(TEXTS[get_lang(db, message.from_user.id)]["blocked"])
        return False
    return True

@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, db):
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
async def set_ru(message: Message, db):
    db.set_language(message.from_user.id, "ru")
    await message.answer(TEXTS["ru"]["language_selected"], reply_markup=main_menu_kb("ru"))

@router.message(F.text == "🇬🇧 English")
async def set_en(message: Message, db):
    db.set_language(message.from_user.id, "en")
    await message.answer(TEXTS["en"]["language_selected"], reply_markup=main_menu_kb("en"))

@router.message(F.text.in_(["🌍 Смена языка", "🌍 Change language"]))
async def change_lang(message: Message):
    await message.answer(TEXTS["ru"]["choose_language"], reply_markup=language_kb())

@router.message(F.text.in_(["🛟 Поддержка", "🛟 Support"]))
async def support(message: Message, db, config):
    if not await ensure_not_blocked(message, db):
        return
    lang = get_lang(db, message.from_user.id)
    await message.answer(t(lang, "support", support=config.support_username), reply_markup=main_menu_kb(lang))

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
        reply_markup=main_menu_kb(lang),
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
async def rates_pick(message: Message, db, rate_service, state: FSMContext):
    lang = get_lang(db, message.from_user.id)
    quote = (message.text or "").strip().upper()
    if quote not in QUOTE_CURRENCIES:
        await message.answer(TEXTS[lang]["invalid_currency"], reply_markup=quote_currency_kb())
        return
    table = await rate_service.get_table(quote)
    body = "\n".join(f"• 1 {cur} = `{val}` {quote}" for cur, val in table.items() if cur != quote)
    await state.clear()
    await message.answer(t(lang, "rates_fmt", quote=quote, body=body), parse_mode="Markdown", reply_markup=main_menu_kb(lang))

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
    cur = (message.text or "").strip().upper()
    if cur not in CURRENCIES:
        await message.answer(TEXTS[lang]["invalid_currency"], reply_markup=currency_kb())
        return
    await state.update_data(from_currency=cur)
    await state.set_state(ExchangeForm.to_currency)
    await message.answer(TEXTS[lang]["choose_to"], reply_markup=currency_kb(exclude=cur))

@router.message(ExchangeForm.to_currency)
async def exchange_to(message: Message, db, state: FSMContext):
    lang = get_lang(db, message.from_user.id)
    cur = (message.text or "").strip().upper()
    data = await state.get_data()
    if cur not in CURRENCIES:
        await message.answer(TEXTS[lang]["invalid_currency"], reply_markup=currency_kb(exclude=data.get("from_currency")))
        return
    if cur == data.get("from_currency"):
        await message.answer(TEXTS[lang]["same_currency"], reply_markup=currency_kb(exclude=data.get("from_currency")))
        return
    await state.update_data(to_currency=cur)
    await state.set_state(ExchangeForm.amount)
    await message.answer(TEXTS[lang]["enter_amount"], reply_markup=remove_kb())

@router.message(ExchangeForm.amount)
async def exchange_amount(message: Message, db, config, rate_service, state: FSMContext):
    lang = get_lang(db, message.from_user.id)
    raw = (message.text or "").replace(",", ".").strip()
    try:
        amount = float(raw)
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer(TEXTS[lang]["invalid_amount"], reply_markup=remove_kb())
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
    await message.answer(TEXTS[lang]["enter_receive"], reply_markup=remove_kb())

@router.message(ExchangeForm.receive_details)
async def exchange_receive(message: Message, db, state: FSMContext):
    lang = get_lang(db, message.from_user.id)
    await state.update_data(receive_details=(message.text or "").strip())
    await state.set_state(ExchangeForm.payment_method)
    await message.answer(TEXTS[lang]["choose_payment"], reply_markup=payment_method_kb(lang))

@router.message(ExchangeForm.payment_method)
async def exchange_payment(message: Message, db, config, state: FSMContext, bot):
    lang = get_lang(db, message.from_user.id)
    text = (message.text or "").strip()

    if text in ["🪙 Крипта", "🪙 Crypto"]:
        await _finalize_request(message, state, db, config, lang, "crypto", "-")
        return
    if text in ["⚡ СБП", "⚡ SBP"]:
        await _finalize_request(message, state, db, config, lang, "sbp", "-")
        return
    if text in ["💳 Карта", "💳 Card"]:
        await message.answer(TEXTS[lang]["choose_card_submethod"], reply_markup=card_submethod_kb(lang))
        return
    if text in ["💳 Номер карты", "💳 Card number"]:
        await _finalize_request(message, state, db, config, lang, "card", "card_number")
        return
    if text == "💬 Telegram Wallet":
        request_id = await _finalize_request(message, state, db, config, lang, "card", "tg_wallet", wallet_mode=True)
        row = db.get_request_by_id(request_id)
        admin_text = t(
            "ru",
            "admin_wallet_urgent",
            request_id=row["id"],
            user_display=user_display(row["username"], row["user_id"]),
            user_id=row["user_id"],
            profile_link=user_profile_link(row["user_id"]),
            from_cur=row["from_currency"],
            to_cur=row["to_currency"],
            amount_from=row["amount_from"],
            amount_to=row["amount_to"],
            receive_details=row["receive_details"],
        )
        db.update_request_status(request_id, "wallet_operator")
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(admin_id, admin_text, parse_mode="Markdown")
            except Exception:
                pass
        await message.answer(t(lang, "wallet_operator_msg", support=config.support_username), reply_markup=main_menu_kb(lang))
        return

    await message.answer(TEXTS[lang]["choose_payment"], reply_markup=payment_method_kb(lang))

async def _finalize_request(message, state, db, config, lang, method, submethod, wallet_mode=False):
    data = await state.get_data()
    method_labels = {
        "ru": {"crypto": "Крипта", "sbp": "СБП", "card": "Карта"},
        "en": {"crypto": "Crypto", "sbp": "SBP", "card": "Card"},
    }
    sub_labels = {
        "ru": {"card_number": "Номер карты", "tg_wallet": "Telegram Wallet", "-": "-"},
        "en": {"card_number": "Card number", "tg_wallet": "Telegram Wallet", "-": "-"},
    }
    payment_url = {
        "crypto": config.crypto_payment_url,
        "sbp": config.sbp_payment_url,
        "card": config.card_payment_url,
    }[method]

    request_id = db.create_exchange_request(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        from_currency=data["from_currency"],
        to_currency=data["to_currency"],
        amount_from=data["amount_from"],
        amount_to=data["amount_to"],
        receive_details=data["receive_details"],
        payment_method=method_labels[lang][method],
        payment_submethod=sub_labels[lang][submethod],
        payment_url=payment_url,
        status="waiting_payment",
    )
    await state.clear()

    if wallet_mode:
        return request_id

    if method == "card" and submethod == "card_number":
        await message.answer(t(lang, "card_number_payment", card_number=config.card_number), parse_mode="Markdown", reply_markup=paid_kb(lang))
    else:
        await message.answer(t(lang, "request_created", request_id=request_id, payment_method=method_labels[lang][method], payment_url=payment_url), parse_mode="Markdown", reply_markup=paid_kb(lang))
    return request_id

@router.message(F.text.in_(["✅ Я оплатил", "✅ I paid"]))
async def mark_paid(message: Message, db, config, bot):
    lang = get_lang(db, message.from_user.id)
    request_row = db.get_active_request(message.from_user.id)
    if not request_row or request_row["status"] != "waiting_payment":
        await message.answer(TEXTS[lang]["no_active_request"], reply_markup=main_menu_kb(lang))
        return

    db.update_request_status(request_row["id"], "paid_pending_review")
    await message.answer(t(lang, "paid_thanks", support=config.support_username), reply_markup=main_menu_kb(lang))

    admin_text = t(
        "ru",
        "admin_new_paid",
        request_id=request_row["id"],
        user_display=user_display(request_row["username"], request_row["user_id"]),
        user_id=request_row["user_id"],
        profile_link=user_profile_link(request_row["user_id"]),
        from_cur=request_row["from_currency"],
        to_cur=request_row["to_currency"],
        amount_from=request_row["amount_from"],
        amount_to=request_row["amount_to"],
        receive_details=request_row["receive_details"],
        payment_method=f"{request_row['payment_method']} / {request_row['payment_submethod'] or '-'}",
    )
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except Exception:
            pass
