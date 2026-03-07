from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from i18n import t


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="English", callback_data="lang:en"),
            ]
        ]
    )


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "new_request")), KeyboardButton(text=t(lang, "rates"))],
            [KeyboardButton(text=t(lang, "admin"))],
        ],
        resize_keyboard=True,
    )


def admin_request_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{request_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{request_id}"),
            ]
        ]
    )
