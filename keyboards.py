from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from i18n import t

CURRENCIES = ["BTC", "USDT", "TON", "RUB", "INR", "USD", "EUR"]

def main_menu_kb(language: str, is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=t(language, "exchange")), KeyboardButton(text=t(language, "rates"))],
        [KeyboardButton(text=t(language, "referral")), KeyboardButton(text=t(language, "support"))],
        [KeyboardButton(text=t(language, "change_language"))],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=t(language, "admin_panel"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def currency_keyboard(prefix: str) -> InlineKeyboardMarkup:
    rows, row = [], []
    for i, c in enumerate(CURRENCIES, start=1):
        row.append(InlineKeyboardButton(text=c, callback_data=f"{prefix}:{c}"))
        if i % 3 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Cancel", callback_data="cancel_flow")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(language, "confirm_request"), callback_data="confirm_exchange")],
        [InlineKeyboardButton(text=t(language, "cancel"), callback_data="cancel_flow")],
    ])

def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
         InlineKeyboardButton(text="English", callback_data="lang:en")]
    ])

def admin_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/admin_stats"), KeyboardButton(text="/admin_requests")],
                  [KeyboardButton(text=t(language, "back_to_menu"))]],
        resize_keyboard=True,
    )
