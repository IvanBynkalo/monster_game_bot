from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message()
async def unknown_message_handler(message: Message):
    logger.warning(
        "UNHANDLED MESSAGE | user_id=%s | text=%r | chat_id=%s",
        message.from_user.id if message.from_user else None,
        message.text,
        message.chat.id if message.chat else None,
    )
    await message.answer(
        "Не понял команду.\n"
        "Попробуй воспользоваться кнопками меню."
    )


@router.callback_query()
async def unknown_callback_handler(callback: CallbackQuery):
    logger.warning(
        "UNHANDLED CALLBACK | user_id=%s | data=%r | message_id=%s",
        callback.from_user.id if callback.from_user else None,
        callback.data,
        callback.message.message_id if callback.message else None,
    )
    await callback.answer("Кнопка пока не обработана", show_alert=False)
