"""
auction_service.py — Аукцион редких предметов.

Раз в 3 дня появляется 3 новых лота:
- Редкий кристалл
- Эмбрион монстра (гарантированная редкость)
- Особый предмет (карта аномалии, приманка, трофей)

Механика: ставки, автобид, завершение через N часов.
"""
import random
import time
from database.repositories import get_connection, add_resource, _update_player_field

import os as _os
# Для тестирования: AUCTION_HOURS=0.016 (1 минута)
# Для теста: установи AUCTION_HOURS=0.016 в Railway (= 1 минута)
AUCTION_REFRESH_HOURS = float(_os.environ.get("AUCTION_HOURS", "72"))
AUCTION_DURATION_HOURS = float(_os.environ.get("AUCTION_DURATION", str(AUCTION_REFRESH_HOURS)))
BID_INCREMENT_PCT = 0.10    # минимальный шаг ставки 10%

# Пул лотов аукциона
AUCTION_POOL = [
    # Кристаллы
    {"type": "crystal", "template": "amber_vessel",    "start_price": 180, "min_level": 3},
    {"type": "crystal", "template": "crimson_crystal",  "start_price": 180, "min_level": 3},
    {"type": "crystal", "template": "shadow_shard",     "start_price": 160, "min_level": 4},
    {"type": "crystal", "template": "cut_quartz",       "start_price": 90,  "min_level": 2},
    # Монстры (эмбрионы)
    {"type": "monster_egg", "monster": "Лунный спрайт", "rarity": "epic",
     "mood": "sadness", "monster_type": "spirit", "hp": 45, "attack": 12,
     "start_price": 300, "min_level": 5,
     "desc": "Редкий духовный монстр с высокой резистентностью."},
    {"type": "monster_egg", "monster": "Кристальный страж", "rarity": "epic",
     "mood": "instinct", "monster_type": "void", "hp": 50, "attack": 10,
     "start_price": 350, "min_level": 5,
     "desc": "Защитник кристаллов. Усиливается связью с кристаллом."},
    {"type": "monster_egg", "monster": "Грозовой щенок", "rarity": "rare",
     "mood": "joy", "monster_type": "storm", "hp": 35, "attack": 9,
     "start_price": 200, "min_level": 4,
     "desc": "Молодой грозовой монстр с высоким потенциалом роста."},
    # Особые предметы
    {"type": "item", "item_slug": "flee_elixir",    "amount": 3, "start_price": 120, "min_level": 1,
     "desc": "3× Эликсир побега — гарантированный уход из боя"},
    {"type": "item", "item_slug": "revival_shard",  "amount": 1, "start_price": 200, "min_level": 3,
     "desc": "Осколок возрождения — оживляет павшего монстра"},
    {"type": "item", "item_slug": "crystal_shard",  "amount": 5, "start_price": 80,  "min_level": 1,
     "desc": "5× Осколок кристалла — материал для Геммы"},
]


def _ensure_auction_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auction_lots (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_type     TEXT NOT NULL,
                lot_data     TEXT NOT NULL,
                start_price  INTEGER NOT NULL,
                current_bid  INTEGER NOT NULL,
                top_bidder   INTEGER DEFAULT NULL,
                ends_at      INTEGER NOT NULL,
                is_active    INTEGER NOT NULL DEFAULT 1,
                claimed      INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auction_bids (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id      INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                amount      INTEGER NOT NULL,
                placed_at   INTEGER NOT NULL
            )
        """)
        conn.commit()


_auction_ok = False
def _lazy():
    global _auction_ok
    if not _auction_ok:
        _ensure_auction_tables()
        _auction_ok = True


def _serialize(data: dict) -> str:
    import json
    return json.dumps(data, ensure_ascii=False)

def _deserialize(s: str) -> dict:
    import json
    return json.loads(s)


def force_reset_auction():
    """Принудительно сбрасывает и пересоздаёт аукцион (для тестирования)."""
    _lazy()
    with get_connection() as conn:
        conn.execute("UPDATE auction_lots SET is_active=0")
        conn.commit()
    refresh_auction_if_needed()


def refresh_auction_if_needed():
    """Создаёт новые лоты если аукцион пуст или истёк."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        active = conn.execute(
            "SELECT COUNT(*) FROM auction_lots WHERE is_active=1 AND ends_at > ?",
            (now,)
        ).fetchone()[0]
    if active > 0:
        return

    # Завершаем старые лоты
    _finish_expired_lots()

    # Создаём 3 новых лота
    ends_at = now + int(AUCTION_DURATION_HOURS * 3600)
    selected = random.sample(AUCTION_POOL, min(3, len(AUCTION_POOL)))
    with get_connection() as conn:
        for lot in selected:
            conn.execute("""
                INSERT INTO auction_lots
                (lot_type, lot_data, start_price, current_bid, ends_at, is_active)
                VALUES (?,?,?,?,?,1)
            """, (lot["type"], _serialize(lot), lot["start_price"], lot["start_price"], ends_at))
        conn.commit()


def _finish_expired_lots():
    """Завершает истёкшие лоты и выдаёт призы победителям."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        lots = conn.execute(
            "SELECT * FROM auction_lots WHERE is_active=1 AND ends_at <= ? AND claimed=0",
            (now,)
        ).fetchall()

    for lot in lots:
        lot = dict(lot)
        if lot["top_bidder"] and not lot["claimed"]:
            _deliver_lot(lot["top_bidder"], lot)
        with get_connection() as conn:
            conn.execute(
                "UPDATE auction_lots SET is_active=0, claimed=1 WHERE id=?",
                (lot["id"],)
            )
            conn.commit()


def _deliver_lot(telegram_id: int, lot: dict):
    """Выдаёт выигранный лот игроку."""
    data = _deserialize(lot["lot_data"])

    if lot["lot_type"] == "crystal":
        from game.crystal_service import create_crystal
        crystal = create_crystal(telegram_id, data["template"])
        # Уведомление
        try:
            from game.notification_service import create_notification
            create_notification(telegram_id, "🏆 Аукцион выигран!",
                f"Поздравляем! {crystal['name']} твой.")
        except Exception:
            pass

    elif lot["lot_type"] == "monster_egg":
        from database.repositories import add_captured_monster
        from game.crystal_service import auto_store_new_monster
        m = add_captured_monster(
            telegram_id, data["monster"], data["rarity"], data["mood"],
            data["hp"], data.get("attack", 8), source_type="auction"
        )
        if m:
            auto_store_new_monster(telegram_id, m["id"])
        try:
            from game.notification_service import create_notification
            create_notification(telegram_id, "🏆 Аукцион выигран!",
                f"Монстр {data['monster']} добавлен в твои кристаллы.")
        except Exception:
            pass

    elif lot["lot_type"] == "item":
        add_resource(telegram_id, data["item_slug"], data.get("amount", 1))
        try:
            from game.notification_service import create_notification
            create_notification(telegram_id, "🏆 Аукцион выигран!",
                f"Получено: {data['item_slug']} ×{data.get('amount', 1)}")
        except Exception:
            pass


def get_active_lots() -> list[dict]:
    """Активные лоты аукциона."""
    _lazy()
    refresh_auction_if_needed()
    now = int(time.time())
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM auction_lots WHERE is_active=1 AND ends_at > ? ORDER BY id",
            (now,)
        ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["data"] = _deserialize(d["lot_data"])
        d["time_left"] = d["ends_at"] - now
        result.append(d)
    return result


def place_bid(telegram_id: int, lot_id: int, amount: int, gold: int) -> tuple[bool, str, int]:
    """Делает ставку."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        lot = conn.execute(
            "SELECT * FROM auction_lots WHERE id=? AND is_active=1 AND ends_at > ?",
            (lot_id, now)
        ).fetchone()
    if not lot:
        return False, "Лот не найден или аукцион завершён.", gold

    lot = dict(lot)
    min_bid = int(lot["current_bid"] * (1 + BID_INCREMENT_PCT))
    if lot["current_bid"] == lot["start_price"]:
        min_bid = lot["start_price"]

    if amount < min_bid:
        return False, f"Минимальная ставка: {min_bid}з (текущая: {lot['current_bid']}з)", gold
    if gold < amount:
        return False, f"Недостаточно золота! Нужно {amount}з, у тебя {gold}з", gold

    # Возвращаем предыдущему победителю его золото
    if lot["top_bidder"] and lot["top_bidder"] != telegram_id:
        prev_gold = lot["current_bid"]
        with get_connection() as conn:
            conn.execute(
                "UPDATE players SET gold=gold+? WHERE telegram_id=?",
                (prev_gold, lot["top_bidder"])
            )
        try:
            from game.notification_service import create_notification
            create_notification(lot["top_bidder"], "🔔 Аукцион",
                f"Тебя перебили на аукционе! Возвращено {prev_gold}з.")
        except Exception:
            pass

    # Списываем золото и делаем ставку
    with get_connection() as conn:
        conn.execute(
            "UPDATE auction_lots SET current_bid=?, top_bidder=? WHERE id=?",
            (amount, telegram_id, lot_id)
        )
        conn.execute("""
            INSERT INTO auction_bids (lot_id, telegram_id, amount, placed_at)
            VALUES (?,?,?,?)
        """, (lot_id, telegram_id, amount, now))
        conn.commit()

    data = _deserialize(lot["lot_data"])
    lot_name = (data.get("monster") or data.get("item_slug") or
                data.get("template", "лот")).replace("_", " ")
    return True, f"✅ Ставка {amount}з принята на «{lot_name}»!", gold - amount


def _fmt_time(seconds: int) -> str:
    if seconds < 3600:
        return f"{seconds // 60} мин."
    if seconds < 86400:
        return f"{seconds // 3600} ч."
    return f"{seconds // 86400} д."


def render_auction(telegram_id: int) -> str:
    """Текст экрана аукциона."""
    lots = get_active_lots()
    if not lots:
        return "🏛 Аукцион\n\nСейчас нет активных лотов. Приходи через 3 дня!"

    lines = ["🏛 Аукцион редкостей\n"]
    for i, lot in enumerate(lots, 1):
        data = lot["data"]
        time_left = _fmt_time(lot["time_left"])
        is_winning = lot["top_bidder"] == telegram_id

        if lot["lot_type"] == "crystal":
            from game.crystal_service import CRYSTAL_TEMPLATES
            tmpl = CRYSTAL_TEMPLATES.get(data.get("template"), {})
            name = tmpl.get("name", "Кристалл")
            desc = tmpl.get("desc", "")
        elif lot["lot_type"] == "monster_egg":
            name = f"🥚 {data.get('monster', 'Монстр')} ({data.get('rarity','')})"
            desc = data.get("desc", "")
        else:
            name = data.get("item_slug", "Предмет").replace("_", " ")
            desc = data.get("desc", f"×{data.get('amount', 1)}")

        winner_mark = " 🏆 ТЫ ЛИДИРУЕШЬ" if is_winning else ""
        lines.append(
            f"Лот {i}: {name}\n"
            f"  {desc}\n"
            f"  💰 Текущая ставка: {lot['current_bid']}з{winner_mark}\n"
            f"  ⏱ До конца: {time_left}"
        )
    return "\n\n".join(lines)
