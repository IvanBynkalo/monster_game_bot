import time
import traceback
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from utils.logger import get_logger, get_events_logger

logger = get_logger(__name__)
events_logger = get_events_logger()


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        started_at = time.perf_counter()

        user_id = None
        username = None
        text = None
        callback_data = None
        event_type = type(event).__name__

        try:
            if isinstance(event, Message):
                if event.from_user:
                    user_id = event.from_user.id
                    username = event.from_user.username
                text = event.text or event.caption

                events_logger.info(
                    "INCOMING_MESSAGE | user_id=%s | username=%s | text=%r",
                    user_id,
                    username,
                    text,
                )

            elif isinstance(event, CallbackQuery):
                if event.from_user:
                    user_id = event.from_user.id
                    username = event.from_user.username
                callback_data = event.data

                events_logger.info(
                    "INCOMING_CALLBACK | user_id=%s | username=%s | data=%r",
                    user_id,
                    username,
                    callback_data,
                )

            result = await handler(event, data)

            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

            logger.info(
                "EVENT_OK | type=%s | user_id=%s | username=%s | text=%r | callback=%r | duration_ms=%s",
                event_type,
                user_id,
                username,
                text,
                callback_data,
                duration_ms,
            )

            return result

        except Exception as e:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            tb = traceback.format_exc()

            logger.error(
                "EVENT_FAIL | type=%s | user_id=%s | username=%s | text=%r | callback=%r | duration_ms=%s | error=%s\n%s",
                event_type,
                user_id,
                username,
                text,
                callback_data,
                duration_ms,
                repr(e),
                tb,
            )
            raise
