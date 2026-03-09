from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


CURRENCIES = ["BTC", "USDT", "TON", "USD", "EUR", "INR", "RUB"]
QUOTE_CURRENCIES = ["RUB", "USD", "EUR", "INR"]


def _reply(rows):
    keyboard = [[KeyboardButton(text=item) for item in row] for row in rows]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def remove_kb():
    return ReplyKeyboardRemove()


def language_kb():
    return _reply([["🇷🇺 Русский", "🇬🇧 English"]])


def main_menu_kb(lang: str, is_admin: bool = False):
    if lang == "en":
        rows = [
            ["💱 Exchange", "📊 Rates"],
            ["🎁 Referral program", "🛟 Support"],
            ["🧾 My requests", "🌍 Change language"],
        ]
        if is_admin:
            rows.append(["👨‍💼 Admin"])
        return _reply(rows)

    rows = [
        ["💱 Обменять", "📊 Курс валют"],
        ["🎁 Реферальная программа", "🛟 Поддержка"],
        ["🧾 Мои заявки", "🌍 Смена языка"],
    ]
    if is_admin:
        rows.append(["👨‍💼 Admin"])
    return _reply(rows)


def admin_menu_kb(lang: str):
    if lang == "en":
        return _reply([["📚 Requests"], ["ℹ️ Admin help"], ["⬅️ Back"]])
    return _reply([["📚 Заявки"], ["ℹ️ Помощь админу"], ["⬅️ Назад"]])


def back_kb(lang: str):
    return _reply([["⬅️ Back"]] if lang == "en" else [["⬅️ Назад"]])


def currency_kb(exclude: str | None = None):
    items = [c for c in CURRENCIES if c != exclude]
    rows = []
    row = []
    for item in items:
        row.append(item)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return _reply(rows)


def quote_currency_kb(lang: str = "ru"):
    back = "⬅️ Back" if lang == "en" else "⬅️ Назад"
    return _reply([["RUB", "USD"], ["EUR", "INR"], [back]])


def payment_method_kb(lang: str):
    return payment_method_with_back_kb(lang)


def payment_method_with_back_kb(lang: str):
    if lang == "en":
        rows = [
            ["⚡ SBP", "💳 Card number"],
            ["💬 Telegram Wallet", "BYBIT ID"],
            ["USDT (TRC20)", "TON"],
            ["BTC"],
            ["⬅️ Back"],
        ]
        return _reply(rows)

    rows = [
        ["⚡ СБП", "💳 Номер карты"],
        ["💬 Telegram Wallet", "BYBIT ID"],
        ["USDT (TRC20)", "TON"],
        ["BTC"],
        ["⬅️ Назад"],
    ]
    return _reply(rows)


def card_submethod_kb(lang: str):
    if lang == "en":
        return _reply([["💳 Card number", "💬 Telegram Wallet"]])
    return _reply([["💳 Номер карты", "💬 Telegram Wallet"]])


def card_submethod_with_back_kb(lang: str):
    if lang == "en":
        return _reply([["💳 Card number", "💬 Telegram Wallet"], ["⬅️ Back"]])
    return _reply([["💳 Номер карты", "💬 Telegram Wallet"], ["⬅️ Назад"]])


def crypto_choice_kb(lang: str):
    return _reply([["BYBIT ID", "USDT (TRC20)"], ["TON", "BTC"]])


def crypto_choice_with_back_kb(lang: str):
    if lang == "en":
        return _reply([["BYBIT ID", "USDT (TRC20)"], ["TON", "BTC"], ["⬅️ Back"]])
    return _reply([["BYBIT ID", "USDT (TRC20)"], ["TON", "BTC"], ["⬅️ Назад"]])


def paid_kb(lang: str):
    if lang == "en":
        return _reply([["✅ I paid"], ["⬅️ Back"]])
    return _reply([["✅ Я оплатил"], ["⬅️ Назад"]])


def card_action_kb(lang: str):
    if lang == "en":
        label = "📋 Copy card number"
    else:
        label = "📋 Скопировать номер карты"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data="copy_card")]]
    )


def crypto_selected_action_kb(lang: str, asset: str):
    if lang == "en":
        copy_label = "📋 Copy address"
        qr_label = "📷 Get QR"
    else:
        copy_label = "📋 Скопировать адрес"
        qr_label = "📷 Получить QR"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=copy_label, callback_data=f"copy_crypto:{asset}")],
            [InlineKeyboardButton(text=qr_label, callback_data=f"request_qr:{asset}")],
        ]
    )
