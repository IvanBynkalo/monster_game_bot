import traceback

from aiogram.types import ErrorEvent

from utils.logger import get_logger

logger = get_logger(__name__)


async def global_error_handler(event: ErrorEvent):
    update = event.update
    exception = event.exception

    user_id = None
    username = None
    text = None
    callback_data = None

    try:
        if update.message:
            if update.message.from_user:
                user_id = update.message.from_user.id
                username = update.message.from_user.username
            text = update.message.text or update.message.caption

        elif update.callback_query:
            if update.callback_query.from_user:
                user_id = update.callback_query.from_user.id
                username = update.callback_query.from_user.username
            callback_data = update.callback_query.data

        tb = "".join(
            traceback.format_exception(
                type(exception),
                exception,
                exception.__traceback__,
            )
        )

        logger.error(
            "GLOBAL_ERROR | user_id=%s | username=%s | text=%r | callback=%r | error=%s\n%s",
            user_id,
            username,
            text,
            callback_data,
            repr(exception),
            tb,
        )

        # Возвращаем True, чтобы aiogram считал ошибку обработанной
        return True

    except Exception as inner_exc:
        logger.exception("ERROR_HANDLER_FAIL: %r", inner_exc)
        return True
