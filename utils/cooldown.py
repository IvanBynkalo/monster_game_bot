"""
Антиспам и cooldown-система (рекомендация #2).
Хранит время последнего действия в памяти — достаточно для одного процесса.
"""
import time
from collections import defaultdict

_last_action: dict[int, float] = defaultdict(float)
_last_combat: dict[int, float] = defaultdict(float)
_last_gather: dict[int, float] = defaultdict(float)
_last_explore: dict[int, float] = defaultdict(float)


def check_cooldown(user_id: int, kind: str = "action", seconds: float = 1.5) -> tuple[bool, float]:
    """
    Возвращает (allowed, wait_seconds).
    allowed=True если cooldown прошёл, False — нужно подождать.
    """
    store = {
        "action":  _last_action,
        "combat":  _last_combat,
        "gather":  _last_gather,
        "explore": _last_explore,
    }.get(kind, _last_action)

    now  = time.monotonic()
    last = store[user_id]
    elapsed = now - last
    if elapsed < seconds:
        return False, round(seconds - elapsed, 1)
    store[user_id] = now
    return True, 0.0


def reset_cooldown(user_id: int, kind: str = "action"):
    store = {
        "action":  _last_action,
        "combat":  _last_combat,
        "gather":  _last_gather,
        "explore": _last_explore,
    }.get(kind, _last_action)
    store[user_id] = 0.0


async def cooldown_guard(message, kind: str = "action", seconds: float = 1.5) -> bool:
    """
    Хелпер для хендлеров. Если cooldown не прошёл — отвечает пользователю
    и возвращает False. Хендлер должен сразу вернуться при False.
    """
    allowed, wait = check_cooldown(message.from_user.id, kind, seconds)
    if not allowed:
        await message.answer(f"⏳ Подожди {wait} сек. перед следующим действием.")
        return False
    return True
