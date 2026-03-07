from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_menu_kb("ru"),
    )


@router.message(lambda message: message.text == "Обменять")
async def exchange_handler(message: Message):
    await message.answer(
        "Раздел обмена скоро будет здесь.",
        reply_markup=main_menu_kb("ru"),
    )


@router.message(lambda message: message.text == "Курс валют")
async def rates_handler(message: Message):
    await message.answer(
        "Раздел курсов валют скоро будет здесь.",
        reply_markup=main_menu_kb("ru"),
    )


@router.message(lambda message: message.text == "Реферальная программа")
async def referral_handler(message: Message):
    await message.answer(
        "Реферальная программа скоро будет здесь.",
        reply_markup=main_menu_kb("ru"),
    )


@router.message(lambda message: message.text == "Поддержка")
async def support_handler(message: Message):
    await message.answer(
        "Поддержка: @eeexxxchangerrr",
        reply_markup=main_menu_kb("ru"),
    )


@router.message(lambda message: message.text == "Смена языка")
async def language_handler(message: Message):
    await message.answer(
        "Language switched to English.",
        reply_markup=main_menu_kb("en"),
    )


@router.message(lambda message: message.text == "Exchange")
async def exchange_handler_en(message: Message):
    await message.answer(
        "Exchange section will be here soon.",
        reply_markup=main_menu_kb("en"),
    )


@router.message(lambda message: message.text == "Rates")
async def rates_handler_en(message: Message):
    await message.answer(
        "Rates section will be here soon.",
        reply_markup=main_menu_kb("en"),
    )


@router.message(lambda message: message.text == "Referral program")
async def referral_handler_en(message: Message):
    await message.answer(
        "Referral program section will be here soon.",
        reply_markup=main_menu_kb("en"),
    )


@router.message(lambda message: message.text == "Support")
async def support_handler_en(message: Message):
    await message.answer(
        "Support: @eeexxxchangerrr",
        reply_markup=main_menu_kb("en"),
    )


@router.message(lambda message: message.text == "Change language")
async def language_handler_en(message: Message):
    await message.answer(
        "Язык переключен на русский.",
        reply_markup=main_menu_kb("ru"),
    )


def get_user_router() -> Router:
    return router