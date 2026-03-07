from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_menu_kb, language_kb

router = Router()


# START — только выбор языка
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🌍 Choose language / Выберите язык",
        reply_markup=language_kb()
    )


# RUSSIAN
@router.message(lambda message: message.text == "🇷🇺 Русский")
async def set_russian(message: Message):
    await message.answer(
        "Язык выбран: Русский",
        reply_markup=main_menu_kb("ru")
    )


# ENGLISH
@router.message(lambda message: message.text == "🇬🇧 English")
async def set_english(message: Message):
    await message.answer(
        "Language selected: English",
        reply_markup=main_menu_kb("en")
    )


# RU MENU
@router.message(lambda message: message.text == "Обменять")
async def exchange_ru(message: Message):
    await message.answer("Раздел обмена скоро будет доступен.")


@router.message(lambda message: message.text == "Курс валют")
async def rates_ru(message: Message):
    await message.answer("Раздел курсов валют скоро будет доступен.")


@router.message(lambda message: message.text == "Реферальная программа")
async def referral_ru(message: Message):
    await message.answer("Реферальная программа скоро будет доступна.")


@router.message(lambda message: message.text == "Поддержка")
async def support_ru(message: Message):
    await message.answer("Поддержка: @eeexxxchangerrr")


@router.message(lambda message: message.text == "Смена языка")
async def change_lang_ru(message: Message):
    await message.answer(
        "🌍 Выберите язык",
        reply_markup=language_kb()
    )


# EN MENU
@router.message(lambda message: message.text == "Exchange")
async def exchange_en(message: Message):
    await message.answer("Exchange section will be available soon.")


@router.message(lambda message: message.text == "Rates")
async def rates_en(message: Message):
    await message.answer("Rates section will be available soon.")


@router.message(lambda message: message.text == "Referral program")
async def referral_en(message: Message):
    await message.answer("Referral program will be available soon.")


@router.message(lambda message: message.text == "Support")
async def support_en(message: Message):
    await message.answer("Support: @eeexxxchangerrr")


@router.message(lambda message: message.text == "Change language")
async def change_lang_en(message: Message):
    await message.answer(
        "🌍 Choose language",
        reply_markup=language_kb()
    )


def get_user_router():
    return router