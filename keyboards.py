from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    if lang == "en":
        keyboard = [
            [KeyboardButton(text="Exchange")],
            [KeyboardButton(text="Rates")],
            [KeyboardButton(text="Referral program")],
            [KeyboardButton(text="Support")],
            [KeyboardButton(text="Change language")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="Обменять")],
            [KeyboardButton(text="Курс валют")],
            [KeyboardButton(text="Реферальная программа")],
            [KeyboardButton(text="Поддержка")],
            [KeyboardButton(text="Смена языка")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )