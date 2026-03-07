from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

CURRENCIES = ["BTC", "USDT", "TON", "USD", "EUR", "INR", "RUB"]
QUOTE_CURRENCIES = ["USD", "EUR", "INR", "RUB", "USDT"]


def language_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )


def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    if lang == "en":
        keyboard = [
            [KeyboardButton(text="💱 Exchange")],
            [KeyboardButton(text="📊 Rates")],
            [KeyboardButton(text="🎁 Referral program")],
            [KeyboardButton(text="🛟 Support")],
            [KeyboardButton(text="🌍 Change language")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="💱 Обменять")],
            [KeyboardButton(text="📊 Курс валют")],
            [KeyboardButton(text="🎁 Реферальная программа")],
            [KeyboardButton(text="🛟 Поддержка")],
            [KeyboardButton(text="🌍 Смена языка")],
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def currency_kb(prefix: str, exclude: str | None = None) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cur in CURRENCIES:
        if exclude and cur == exclude:
            continue
        row.append(InlineKeyboardButton(text=cur, callback_data=f"{prefix}:{cur}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_method_kb(lang: str) -> InlineKeyboardMarkup:
    labels = {
        "ru": {"crypto": "🪙 Крипта", "card": "💳 Карта", "sbp": "⚡ СБП"},
        "en": {"crypto": "🪙 Crypto", "card": "💳 Card", "sbp": "⚡ SBP"},
    }[lang]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels["crypto"], callback_data="pay:crypto")],
        [InlineKeyboardButton(text=labels["card"], callback_data="pay:card")],
        [InlineKeyboardButton(text=labels["sbp"], callback_data="pay:sbp")],
    ])


def card_submethod_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "en":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Card number", callback_data="cardsub:card_number")],
            [InlineKeyboardButton(text="💬 Telegram Wallet", callback_data="cardsub:tg_wallet")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Номер карты", callback_data="cardsub:card_number")],
        [InlineKeyboardButton(text="💬 Telegram Wallet", callback_data="cardsub:tg_wallet")],
    ])


def paid_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "en":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ I paid", callback_data="mark_paid")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="mark_paid")],
    ])


def rates_quotes_kb(lang: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cur in QUOTE_CURRENCIES:
        row.append(InlineKeyboardButton(text=cur, callback_data=f"ratesq:{cur}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
