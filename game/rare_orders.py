"""
rare_orders.py — Рынок редких заказов.

NPC в городе выставляют особые заказы:
- кристалл определённого качества/аффинности
- монстр определённой эмоции/редкости
- зверь живьём (в кристалле)
- кристалл с пустым объёмом

Заказы сменяются раз в 24 часа.
Выполнение — разовое, большая награда.
"""
import random
import time
from database.repositories import get_connection

ORDERS_REFRESH_HOURS = 24

RARE_ORDER_POOL = [
    # Заказы на кристаллы
    {
        "id": "order_rare_crystal_rage",
        "title": "🔴 Нужен кристалл Ярости",
        "npc": "Варг",
        "desc": "«Мне нужен кристалл с резонансом Ярости. Любой редкости.»",
        "type": "crystal_affinity",
        "require": {"emotion_affinity": "rage"},
        "reward_gold": 180,
        "reward_exp": 90,
    },
    {
        "id": "order_empty_crystal",
        "title": "⬜ Пустой кристалл",
        "npc": "Гемма",
        "desc": "«Для эксперимента нужен чистый пустой кристалл. Ни одного монстра внутри.»",
        "type": "crystal_empty",
        "require": {"current_monsters": 0},
        "reward_gold": 120,
        "reward_exp": 60,
    },
    {
        "id": "order_rare_monster_joy",
        "title": "🌟 Монстр Радости",
        "npc": "Мирна",
        "desc": "«Клиент хочет монстра с эмоцией Радости. Платит хорошо.»",
        "type": "monster_mood",
        "require": {"mood": "joy"},
        "reward_gold": 250,
        "reward_exp": 125,
    },
    {
        "id": "order_epic_monster",
        "title": "🟣 Эпический монстр",
        "npc": "Варг",
        "desc": "«Знатный охотник ищет эпического монстра любого типа.»",
        "type": "monster_rarity",
        "require": {"rarity": "epic"},
        "reward_gold": 400,
        "reward_exp": 200,
    },
    {
        "id": "order_rare_monster_instinct",
        "title": "🎯 Монстр Инстинкта",
        "npc": "Мирна",
        "desc": "«Нужен монстр с эмоцией Инстинкта — охотник ищет бойца.»",
        "type": "monster_mood",
        "require": {"mood": "instinct"},
        "reward_gold": 220,
        "reward_exp": 110,
    },
    {
        "id": "order_uncommon_monster",
        "title": "🟢 Необычный монстр",
        "npc": "Варг",
        "desc": "«Нужен монстр редкости Необычный или выше. Любой эмоции.»",
        "type": "monster_rarity",
        "require": {"rarity": "uncommon"},
        "reward_gold": 180,
        "reward_exp": 90,
    },
    {
        "id": "order_crystal_joy_filled",
        "title": "🟡 Заполненный янтарный",
        "npc": "Гемма",
        "desc": "«Нужен Янтарный сосуд с хотя бы одним монстром внутри.»",
        "type": "crystal_template_filled",
        "require": {"template_code": "amber_vessel", "min_monsters": 1},
        "reward_gold": 220,
        "reward_exp": 110,
    },
    {
        "id": "order_fear_monster",
        "title": "😱 Монстр Страха",
        "npc": "Варг",
        "desc": "«Один алхимик собирает эссенции страха. Нужен монстр.»",
        "type": "monster_mood",
        "require": {"mood": "fear"},
        "reward_gold": 220,
        "reward_exp": 110,
    },
]


def _ensure_orders_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rare_orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    TEXT NOT NULL,
                expires_at  INTEGER NOT NULL,
                is_active   INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rare_order_completions (
                telegram_id INTEGER NOT NULL,
                order_id    TEXT NOT NULL,
                completed_at INTEGER NOT NULL,
                PRIMARY KEY (telegram_id, order_id)
            )
        """)
        conn.commit()


_orders_ok = False
def _lazy():
    global _orders_ok
    if not _orders_ok:
        _ensure_orders_table()
        _orders_ok = True


def refresh_orders():
    """Обновляет список заказов раз в 24 часа."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        active = conn.execute(
            "SELECT COUNT(*) FROM rare_orders WHERE is_active=1 AND expires_at > ?",
            (now,)
        ).fetchone()[0]
    if active >= 3:
        return

    # Деактивируем старые
    with get_connection() as conn:
        conn.execute("UPDATE rare_orders SET is_active=0 WHERE expires_at <= ?", (now,))
        conn.commit()

    # Выбираем 3-4 новых заказа
    expires_at = now + ORDERS_REFRESH_HOURS * 3600
    selected = random.sample(RARE_ORDER_POOL, min(4, len(RARE_ORDER_POOL)))
    with get_connection() as conn:
        for order in selected:
            exists = conn.execute(
                "SELECT id FROM rare_orders WHERE order_id=? AND is_active=1",
                (order["id"],)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO rare_orders (order_id, expires_at) VALUES (?,?)",
                    (order["id"], expires_at)
                )
        conn.commit()


def get_active_orders(telegram_id: int) -> list[dict]:
    """Активные заказы, которые игрок ещё не выполнял."""
    _lazy()
    refresh_orders()
    now = int(time.time())
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT order_id, expires_at FROM rare_orders WHERE is_active=1 AND expires_at > ?",
            (now,)
        ).fetchall()
        completed = {r["order_id"] for r in conn.execute(
            "SELECT order_id FROM rare_order_completions WHERE telegram_id=?",
            (telegram_id,)
        ).fetchall()}

    order_map = {o["id"]: o for o in RARE_ORDER_POOL}
    result = []
    for row in rows:
        if row["order_id"] in completed:
            continue
        order = order_map.get(row["order_id"])
        if order:
            time_left = row["expires_at"] - now
            hrs = time_left // 3600
            result.append({**order, "expires_in_h": hrs})
    return result


def check_order_fulfillment(telegram_id: int, order: dict) -> bool:
    """Проверяет может ли игрок выполнить заказ прямо сейчас."""
    from database.repositories import get_player_monsters
    from game.crystal_service import get_player_crystals, get_monsters_in_crystal
    req = order["require"]
    otype = order["type"]

    if otype == "crystal_affinity":
        crystals = get_player_crystals(telegram_id)
        return any(c["emotion_affinity"] == req["emotion_affinity"] for c in crystals)

    elif otype == "crystal_empty":
        crystals = get_player_crystals(telegram_id)
        return any(c["current_monsters"] == 0 for c in crystals)

    elif otype == "crystal_template_filled":
        crystals = get_player_crystals(telegram_id)
        for c in crystals:
            if c["template_code"] == req["template_code"] and c["current_monsters"] >= req.get("min_monsters", 1):
                return True
        return False

    elif otype == "monster_mood":
        monsters = get_player_monsters(telegram_id)
        return any(m.get("mood") == req["mood"] and not m.get("is_dead") for m in monsters)

    elif otype == "monster_rarity":
        # Подходит монстр с требуемой редкостью ИЛИ выше
        RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]
        req_idx = RARITY_ORDER.index(req["rarity"]) if req["rarity"] in RARITY_ORDER else 0
        monsters = get_player_monsters(telegram_id)
        return any(
            RARITY_ORDER.index(m.get("rarity","common")) >= req_idx
            and not m.get("is_dead")
            for m in monsters
            if m.get("rarity","common") in RARITY_ORDER
        )

    elif otype == "wildlife_captured":
        monsters = get_player_monsters(telegram_id)
        return any(m.get("name") == req["name"] and m.get("source_type") == "capture"
                   and not m.get("is_dead") for m in monsters)

    return False


def complete_order(telegram_id: int, order_id: str, gold: int) -> tuple[bool, str, int]:
    """Выполняет заказ и выдаёт награду."""
    _lazy()
    order = next((o for o in RARE_ORDER_POOL if o["id"] == order_id), None)
    if not order:
        return False, "Заказ не найден.", gold

    # Проверяем что заказ ещё активен
    now = int(time.time())
    with get_connection() as conn:
        active = conn.execute(
            "SELECT id FROM rare_orders WHERE order_id=? AND is_active=1 AND expires_at > ?",
            (order_id, now)
        ).fetchone()
    if not active:
        return False, "Заказ истёк.", gold

    # Проверяем уже выполнен?
    with get_connection() as conn:
        done = conn.execute(
            "SELECT id FROM rare_order_completions WHERE telegram_id=? AND order_id=?",
            (telegram_id, order_id)
        ).fetchone()
    if done:
        return False, "Ты уже выполнял этот заказ.", gold

    if not check_order_fulfillment(telegram_id, order):
        return False, "Требования не выполнены.", gold

    # Выдаём награду
    from database.repositories import add_player_gold, add_player_experience
    add_player_gold(telegram_id, order["reward_gold"])
    add_player_experience(telegram_id, order["reward_exp"])

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO rare_order_completions (telegram_id, order_id, completed_at) VALUES (?,?,?)",
            (telegram_id, order_id, now)
        )
        conn.commit()

    return True, (
        f"✅ Заказ выполнен: {order['title']}\n"
        f"💰 +{order['reward_gold']} золота\n"
        f"✨ +{order['reward_exp']} опыта"
    ), gold + order["reward_gold"]


def render_orders(telegram_id: int) -> str:
    orders = get_active_orders(telegram_id)
    if not orders:
        return "📋 Рынок заказов\n\nСейчас нет активных заказов. Возвращайся завтра!"

    lines = ["📋 Рынок редких заказов\n"]
    for o in orders:
        can_do = check_order_fulfillment(telegram_id, o)
        status = "✅ Готово к сдаче" if can_do else "❌ Требования не выполнены"
        lines.append(
            f"{o['title']}\n"
            f"  NPC: {o['npc']}\n"
            f"  {o['desc']}\n"
            f"  💰 Награда: {o['reward_gold']}з | Истекает через: {o['expires_in_h']}ч\n"
            f"  {status}"
        )
    return "\n\n".join(lines)
