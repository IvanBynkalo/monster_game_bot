from aiogram.types import CallbackQuery, Message


def extract_update_context(obj):
    context = {
        "user_id": None,
        "username": None,
        "text": None,
        "callback_data": None,
    }

    if isinstance(obj, Message):
        if obj.from_user:
            context["user_id"] = obj.from_user.id
            context["username"] = obj.from_user.username
        context["text"] = obj.text or obj.caption

    elif isinstance(obj, CallbackQuery):
        if obj.from_user:
            context["user_id"] = obj.from_user.id
            context["username"] = obj.from_user.username
        context["callback_data"] = obj.data

    return context
