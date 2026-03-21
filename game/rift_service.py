"""
rift_service.py — Разлом: особая точка на карте с ограниченными входами.

Механика:
- Разлом — локация "emotion_rift" с особыми правилами
- Каждый вход тратит "токен разлома" (максимум 3, восполняется 1/день)
- Внутри: редкие монстры, редкие кристаллы, высокий риск
- Монстры нанося больше урона (×1.5)
- Шанс встречи с редким монстром: 35% (vs обычных 18%)
- Шанс найти редкий кристалл при победе: 10%
"""
import time
from database.repositories import get_connection

RIFT_SLUG = "emotion_rift"
MAX_TOKENS = 3
REGEN_INTERVAL = 86400  # 1 день


def _ensure_rift_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_rift_tokens (
                telegram_id  INTEGER PRIMARY KEY,
                tokens       INTEGER NOT NULL DEFAULT 3,
                last_regen   INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()


_rift_ok = False
def _lazy():
    global _rift_ok
    if not _rift_ok:
        _ensure_rift_table()
        _rift_ok = True


def _regen_tokens(telegram_id: int):
    """Восполняет токены (1/день)."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        row = conn.execute(
            "SELECT tokens, last_regen FROM player_rift_tokens WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()
    if not row:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO player_rift_tokens (telegram_id, tokens, last_regen) VALUES (?,3,?)",
                (telegram_id, now)
            )
            conn.commit()
        return

    elapsed = now - row["last_regen"]
    regen = min(MAX_TOKENS - row["tokens"], elapsed // REGEN_INTERVAL)
    if regen > 0:
        new_tokens = min(MAX_TOKENS, row["tokens"] + regen)
        new_regen = row["last_regen"] + regen * REGEN_INTERVAL
        with get_connection() as conn:
            conn.execute(
                "UPDATE player_rift_tokens SET tokens=?, last_regen=? WHERE telegram_id=?",
                (new_tokens, new_regen, telegram_id)
            )
            conn.commit()


def get_tokens(telegram_id: int) -> dict:
    _lazy()
    _regen_tokens(telegram_id)
    now = int(time.time())
    with get_connection() as conn:
        row = conn.execute(
            "SELECT tokens, last_regen FROM player_rift_tokens WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()
    if not row:
        return {"tokens": MAX_TOKENS, "max": MAX_TOKENS, "next_regen_in": REGEN_INTERVAL}

    next_regen = REGEN_INTERVAL - (now - row["last_regen"]) % REGEN_INTERVAL
    return {
        "tokens": row["tokens"],
        "max": MAX_TOKENS,
        "next_regen_in": next_regen,
    }


def spend_token(telegram_id: int) -> tuple[bool, str]:
    """Тратит токен для входа в Разлом."""
    _lazy()
    _regen_tokens(telegram_id)
    info = get_tokens(telegram_id)
    if info["tokens"] <= 0:
        hrs = info["next_regen_in"] // 3600
        mins = (info["next_regen_in"] % 3600) // 60
        return False, (
            f"🔒 Нет токенов для входа в Разлом!\n"
            f"Следующий токен через: {hrs}ч {mins}м\n"
            f"(Максимум {MAX_TOKENS} входа в день)"
        )
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_rift_tokens SET tokens=tokens-1 WHERE telegram_id=?",
            (telegram_id,)
        )
        conn.commit()
    remaining = info["tokens"] - 1
    return True, f"⚡ Вход в Разлом! Осталось входов сегодня: {remaining}/{MAX_TOKENS}"


def is_in_rift(location_slug: str) -> bool:
    return location_slug == RIFT_SLUG


def get_rift_encounter_modifiers() -> dict:
    """Боевые модификаторы внутри Разлома."""
    return {
        "monster_chance": 35,     # вместо обычных 18%
        "enemy_damage_mult": 1.5, # враги бьют в 1.5 раза сильнее
        "rare_crystal_drop": 0.10, # 10% шанс кристалла после победы
        "loot_bonus": 0.30,       # +30% к лоту
    }


def try_drop_crystal(telegram_id: int) -> str | None:
    """10% шанс выпадения кристалла после победы в Разломе."""
    import random
    mods = get_rift_encounter_modifiers()
    if random.random() > mods["rare_crystal_drop"]:
        return None
    templates = ["amber_vessel", "crimson_crystal", "shadow_shard", "cut_quartz"]
    template = random.choice(templates)
    from game.crystal_service import create_crystal, can_add_crystal
    ok, _ = can_add_crystal(telegram_id, "on_hand")
    if not ok:
        # Ставим к Варгу если нет места
        from game.crystal_service import can_add_crystal as _cac
        ok2, _ = _cac(telegram_id, "varg")
        if not ok2:
            return None
    crystal = create_crystal(telegram_id, template)
    return f"💎 Разлом подарил тебе: {crystal['name']}!"


def render_rift_status(telegram_id: int) -> str:
    info = get_tokens(telegram_id)
    bar = "🔵" * info["tokens"] + "⚫" * (info["max"] - info["tokens"])
    hrs = info["next_regen_in"] // 3600
    mins = (info["next_regen_in"] % 3600) // 60
    return (
        f"🌌 Разлом Эмоций\n\n"
        f"Входы: {bar} {info['tokens']}/{info['max']}\n"
        f"Следующий вход через: {hrs}ч {mins}м\n\n"
        f"⚠️ Внутри:\n"
        f"• Монстры бьют в 1.5× сильнее\n"
        f"• Шанс редких встреч: 35%\n"
        f"• 10% шанс получить кристалл после победы\n"
        f"• Каждый вход тратит 1 токен"
    )
