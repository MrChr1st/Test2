from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

CURRENCIES = ["BTC", "USDT", "TON", "USD", "EUR", "INR", "RUB"]
QUOTE_CURRENCIES = ["USD", "EUR", "INR", "RUB", "USDT"]

def _make(rows):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=x) for x in row] for row in rows],
        resize_keyboard=True
    )

def remove_kb():
    return ReplyKeyboardRemove()

def language_kb():
    return _make([["🇷🇺 Русский", "🇬🇧 English"]])

def main_menu_kb(lang: str):
    if lang == "en":
        return _make([
            ["💱 Exchange", "📊 Rates"],
            ["🎁 Referral program", "🛟 Support"],
            ["🌍 Change language"],
        ])
    return _make([
        ["💱 Обменять", "📊 Курс валют"],
        ["🎁 Реферальная программа", "🛟 Поддержка"],
        ["🌍 Смена языка"],
    ])

def currency_kb(exclude=None):
    items = [c for c in CURRENCIES if c != exclude]
    rows = [items[i:i+3] for i in range(0, len(items), 3)]
    return _make(rows)

def quote_currency_kb():
    rows = [QUOTE_CURRENCIES[i:i+3] for i in range(0, len(QUOTE_CURRENCIES), 3)]
    return _make(rows)

def payment_method_kb(lang: str):
    return _make([["🪙 Crypto", "💳 Card", "⚡ SBP"]] if lang == "en" else [["🪙 Крипта", "💳 Карта", "⚡ СБП"]])

def card_submethod_kb(lang: str):
    return _make([["💳 Card number", "💬 Telegram Wallet"]] if lang == "en" else [["💳 Номер карты", "💬 Telegram Wallet"]])

def paid_kb(lang: str):
    return _make([["✅ I paid"]] if lang == "en" else [["✅ Я оплатил"]])
