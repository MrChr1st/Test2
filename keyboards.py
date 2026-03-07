from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

CURRENCIES = ["BTC", "USDT", "TON", "USD", "EUR", "INR", "RUB"]
QUOTE_CURRENCIES = ["USD", "EUR", "INR", "RUB", "USDT"]

def _reply(rows):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=x) for x in row] for row in rows],
        resize_keyboard=True
    )

def remove_kb():
    return ReplyKeyboardRemove()

def language_kb():
    return _reply([["🇷🇺 Русский", "🇬🇧 English"]])

def main_menu_kb(lang: str, is_admin: bool = False):
    rows = (
        [["💱 Exchange", "📊 Rates"], ["🎁 Referral program", "🛟 Support"], ["🌍 Change language"]]
        if lang == "en"
        else [["💱 Обменять", "📊 Курс валют"], ["🎁 Реферальная программа", "🛟 Поддержка"], ["🌍 Смена языка"]]
    )
    if is_admin:
        rows.append(["👨‍💼 Admin"])
    return _reply(rows)

def currency_kb(exclude=None):
    items = [c for c in CURRENCIES if c != exclude]
    return _reply([items[i:i+3] for i in range(0, len(items), 3)])

def quote_currency_kb():
    return _reply([QUOTE_CURRENCIES[i:i+3] for i in range(0, len(QUOTE_CURRENCIES), 3)])

def payment_method_kb(lang: str):
    return _reply([["🪙 Crypto", "💳 Card", "⚡ SBP"]] if lang == "en" else [["🪙 Крипта", "💳 Карта", "⚡ СБП"]])

def card_submethod_kb(lang: str):
    return _reply([["💳 Card number", "💬 Telegram Wallet"]] if lang == "en" else [["💳 Номер карты", "💬 Telegram Wallet"]])

def paid_kb(lang: str):
    return _reply([["✅ I paid"]] if lang == "en" else [["✅ Я оплатил"]])

def admin_menu_kb(lang: str):
    return _reply([["📚 Requests"], ["ℹ️ Admin help"]] if lang == "en" else [["📚 Заявки"], ["ℹ️ Помощь админу"]])


def crypto_choice_kb(lang: str):
    rows = (
        [["BYBIT ID", "USDT (TRC20)"], ["TON", "BTC"]]
        if lang == "en"
        else [["BYBIT ID", "USDT (TRC20)"], ["TON", "BTC"]]
    )
    return _reply(rows)

def crypto_selected_action_kb(lang: str, asset: str):
    labels = {
        "en": {
            "copy": "📋 Copy address",
            "qr": "📷 Get QR",
        },
        "ru": {
            "copy": "📋 Скопировать адрес",
            "qr": "📷 Получить QR",
        },
    }[lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=labels["copy"], callback_data=f"copy_crypto:{asset}")],
            [InlineKeyboardButton(text=labels["qr"], callback_data=f"request_qr:{asset}")],
        ]
    )

def card_action_kb(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=("📋 Copy card number" if lang == "en" else "📋 Скопировать номер карты"), callback_data="copy_card")],
        ]
    )



def back_kb(lang: str):
    return _reply([["⬅️ Back"]] if lang == "en" else [["⬅️ Назад"]])

def payment_method_with_back_kb(lang: str):
    return _reply([["🪙 Crypto", "💳 Card", "⚡ SBP"], ["⬅️ Back"]] if lang == "en" else [["🪙 Крипта", "💳 Карта", "⚡ СБП"], ["⬅️ Назад"]])

def card_submethod_with_back_kb(lang: str):
    return _reply([["💳 Card number", "💬 Telegram Wallet"], ["⬅️ Back"]] if lang == "en" else [["💳 Номер карты", "💬 Telegram Wallet"], ["⬅️ Назад"]])

def crypto_choice_with_back_kb(lang: str):
    return _reply([["BYBIT ID", "USDT (TRC20)"], ["TON", "BTC"], ["⬅️ Back"]] if lang == "en" else [["BYBIT ID", "USDT (TRC20)"], ["TON", "BTC"], ["⬅️ Назад"]])
