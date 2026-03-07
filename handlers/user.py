import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()


async def send_admin_targets(bot, config, text: str):
    """
    Отправка уведомлений админу и в канал
    """

    targets = []

    # админы
    for admin_id in config.admin_ids:
        targets.append(admin_id)

    # канал
    if getattr(config, "channel_target", None):
        channel = config.channel_target

        try:
            if isinstance(channel, str) and channel.startswith("-100"):
                channel = int(channel)
        except Exception:
            pass

        targets.append(channel)

    # отправка
    for target in targets:
        try:
            await bot.send_message(target, text, parse_mode="Markdown")
            logging.warning(f"Notification sent to {target}")
        except Exception as e:
            logging.exception(f"Failed to send notification to {target}: {e}")


@router.message(F.text == "/testnotify")
async def test_notify(message: Message, config, bot):
    """
    Тестовая команда для проверки уведомлений
    """

    text = "✅ Тестовое уведомление работает"

    await send_admin_targets(bot, config, text)

    await message.answer("Уведомление отправлено")