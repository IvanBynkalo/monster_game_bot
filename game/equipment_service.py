"""
equipment_service.py — Система экипировки персонажа.

Слоты: belt (ремень), boots (сапоги), hat (шляпа), suit (комбез)
Хранение: отдельная таблица player_equipment
Эффекты применяются через get_equipment_bonuses()
"""
from database.repositories import get_connection

# ── Каталог предметов экипировки ──────────────────────────────────────────────

EQUIPMENT_CATALOG = {
    # ── РЕМНИ (хранение кристаллов) ──────────────────────────────────────────
    "belt_basic":    {"name": "🪢 Простой ремень",      "slot": "belt", "crystal_slots": 1, "price": 60,  "desc": "1 слот для кристаллов"},
    "belt_leather":  {"name": "🪢 Кожаный ремень",      "slot": "belt", "crystal_slots": 2, "price": 150, "desc": "2 слота для кристаллов"},
    "belt_reinforced":{"name": "🪢 Усиленный ремень",   "slot": "belt", "crystal_slots": 3, "price": 300, "desc": "3 слота для кристаллов"},
    "belt_master":   {"name": "🪢 Ремень мастера",      "slot": "belt", "crystal_slots": 4, "price": 600, "desc": "4 слота для кристаллов"},
    "belt_legendary":{"name": "🪢 Легендарный ремень",  "slot": "belt", "crystal_slots": 5, "price": 1200,"desc": "5 слотов для кристаллов"},

    # ── САПОГИ (скорость перехода, износ) ────────────────────────────────────
    "boots_worn":    {"name": "👞 Старые сапоги",        "slot": "boots", "travel_bonus": 0.05, "durability": 30,  "price": 40,   "repair": 15, "desc": "+5% скорость"},
    "boots_leather": {"name": "👞 Кожаные сапоги",       "slot": "boots", "travel_bonus": 0.15, "durability": 60,  "price": 120,  "repair": 40, "desc": "+15% скорость"},
    "boots_ranger":  {"name": "👞 Сапоги следопыта",     "slot": "boots", "travel_bonus": 0.25, "durability": 80,  "price": 280,  "repair": 80, "desc": "+25% скорость"},
    "boots_swift":   {"name": "👞 Быстрые сапоги",       "slot": "boots", "travel_bonus": 0.35, "durability": 100, "price": 550,  "repair": 150,"desc": "+35% скорость"},
    "boots_wind":    {"name": "👞 Сапоги ветра",         "slot": "boots", "travel_bonus": 0.50, "durability": 120, "price": 1000, "repair": 250,"desc": "+50% скорость"},

    # ── ШЛЯПЫ (цены покупки/продажи) ─────────────────────────────────────────
    "hat_old":       {"name": "🎩 Старая шляпа",         "slot": "hat", "buy_discount": 0.03, "sell_bonus": 0.03, "price": 50,  "desc": "-3% цена покупки, +3% продажа"},
    "hat_merchant":  {"name": "🎩 Шляпа торговца",       "slot": "hat", "buy_discount": 0.08, "sell_bonus": 0.08, "price": 200, "desc": "-8% покупка, +8% продажа"},
    "hat_noble":     {"name": "🎩 Дворянская шляпа",     "slot": "hat", "buy_discount": 0.15, "sell_bonus": 0.12, "price": 450, "desc": "-15% покупка, +12% продажа"},
    "hat_master":    {"name": "🎩 Шляпа мастера торговли","slot": "hat", "buy_discount": 0.20, "sell_bonus": 0.20, "price": 900, "desc": "-20% покупка, +20% продажа"},

    # ── КОМБЕЗЫ (скорость восстановления энергии) ────────────────────────────
    "suit_simple":   {"name": "🥻 Простой комбез",       "slot": "suit", "energy_regen": 0.15, "price": 80,  "desc": "+15% скорость регенерации энергии"},
    "suit_traveler": {"name": "🥻 Комбез путешественника","slot": "suit", "energy_regen": 0.30, "price": 200, "desc": "+30% скорость регенерации энергии"},
    "suit_explorer": {"name": "🥻 Комбез исследователя", "slot": "suit", "energy_regen": 0.50, "price": 450, "desc": "+50% скорость регенерации энергии"},
    "suit_elite":    {"name": "🥻 Элитный комбез",       "slot": "suit", "energy_regen": 0.75, "price": 900, "desc": "+75% скорость регенерации энергии"},
}

SLOTS = ["belt", "boots", "hat", "suit"]
SLOT_NAMES = {"belt": "🪢 Ремень", "boots": "👞 Сапоги", "hat": "🎩 Шляпа", "suit": "🥻 Комбез"}


# ── База данных ───────────────────────────────────────────────────────────────

def _ensure_tables():
    with get_connection() as conn:
        # Надетая экипировка
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_equipment (
                telegram_id  INTEGER NOT NULL,
                slot         TEXT    NOT NULL,
                item_slug    TEXT    NOT NULL,
                durability   INTEGER NOT NULL DEFAULT 100,
                PRIMARY KEY (telegram_id, slot)
            )
        """)
        # Инвентарь экипировки (купленные но не надетые)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_equipment_inventory (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER NOT NULL,
                item_slug    TEXT    NOT NULL,
                durability   INTEGER NOT NULL DEFAULT 100
            )
        """)
        # Кристаллы на ремне
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_belt_crystals (
                telegram_id  INTEGER NOT NULL,
                slot_index   INTEGER NOT NULL,
                crystal_slug TEXT,
                PRIMARY KEY (telegram_id, slot_index)
            )
        """)
        conn.commit()


_tables_ok = False
def _lazy():
    global _tables_ok
    if not _tables_ok:
        _ensure_tables()
        _tables_ok = True


# ── Получение/установка экипировки ───────────────────────────────────────────

def get_equipped(telegram_id: int) -> dict[str, dict | None]:
    """Возвращает {slot: {item_slug, durability, ...item_data} | None}"""
    _lazy()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT slot, item_slug, durability FROM player_equipment WHERE telegram_id=?",
            (telegram_id,)
        ).fetchall()
    result = {slot: None for slot in SLOTS}
    for row in rows:
        item = EQUIPMENT_CATALOG.get(row["item_slug"], {})
        result[row["slot"]] = {**item, "slug": row["item_slug"], "durability": row["durability"]}
    return result


def equip_item(telegram_id: int, item_slug: str) -> tuple[bool, str]:
    """Надевает предмет из инвентаря экипировки."""
    _lazy()
    item = EQUIPMENT_CATALOG.get(item_slug)
    if not item:
        return False, "Предмет не найден."
    slot = item["slot"]
    with get_connection() as conn:
        # Проверяем что предмет есть в инвентаре
        row = conn.execute(
            "SELECT id, durability FROM player_equipment_inventory WHERE telegram_id=? AND item_slug=? LIMIT 1",
            (telegram_id, item_slug)
        ).fetchone()
        if not row:
            return False, "Этого предмета нет в твоём инвентаре."
        # Снимаем текущий предмет в слоте (кладём в инвентарь)
        old = conn.execute(
            "SELECT item_slug, durability FROM player_equipment WHERE telegram_id=? AND slot=?",
            (telegram_id, slot)
        ).fetchone()
        if old:
            conn.execute(
                "INSERT INTO player_equipment_inventory (telegram_id, item_slug, durability) VALUES (?,?,?)",
                (telegram_id, old["item_slug"], old["durability"])
            )
        # Надеваем новый
        dur = row["durability"]
        conn.execute(
            "INSERT OR REPLACE INTO player_equipment (telegram_id, slot, item_slug, durability) VALUES (?,?,?,?)",
            (telegram_id, slot, item_slug, dur)
        )
        conn.execute("DELETE FROM player_equipment_inventory WHERE id=?", (row["id"],))
        conn.commit()
    return True, f"✅ Надет: {item['name']}"


def unequip_item(telegram_id: int, slot: str) -> tuple[bool, str]:
    """Снимает предмет и кладёт в инвентарь."""
    _lazy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT item_slug, durability FROM player_equipment WHERE telegram_id=? AND slot=?",
            (telegram_id, slot)
        ).fetchone()
        if not row:
            return False, "В этом слоте ничего не надето."
        conn.execute(
            "INSERT INTO player_equipment_inventory (telegram_id, item_slug, durability) VALUES (?,?,?)",
            (telegram_id, row["item_slug"], row["durability"])
        )
        conn.execute("DELETE FROM player_equipment WHERE telegram_id=? AND slot=?", (telegram_id, slot))
        conn.commit()
    item = EQUIPMENT_CATALOG.get(row["item_slug"], {})
    return True, f"✅ Снят: {item.get('name', row['item_slug'])}"


def get_equipment_inventory(telegram_id: int) -> list[dict]:
    """Предметы экипировки в инвентаре (не надетые)."""
    _lazy()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, item_slug, durability FROM player_equipment_inventory WHERE telegram_id=?",
            (telegram_id,)
        ).fetchall()
    result = []
    for row in rows:
        item = EQUIPMENT_CATALOG.get(row["item_slug"], {})
        result.append({**item, "inv_id": row["id"], "slug": row["item_slug"], "durability": row["durability"]})
    return result


def buy_equipment(telegram_id: int, item_slug: str, gold: int) -> tuple[bool, str, int]:
    """Покупает предмет и добавляет в инвентарь. Возвращает (ok, message, new_gold)."""
    _lazy()
    item = EQUIPMENT_CATALOG.get(item_slug)
    if not item:
        return False, "Предмет не найден.", gold
    price = item["price"]
    if gold < price:
        return False, f"Недостаточно золота! Нужно {price}з, у тебя {gold}з", gold
    dur = item.get("durability", 100)
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO player_equipment_inventory (telegram_id, item_slug, durability) VALUES (?,?,?)",
            (telegram_id, item_slug, dur)
        )
        conn.commit()
    return True, f"✅ Куплено: {item['name']}", gold - price


def repair_boots(telegram_id: int, gold: int) -> tuple[bool, str, int]:
    """Ремонт надетых сапог."""
    _lazy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT item_slug, durability FROM player_equipment WHERE telegram_id=? AND slot='boots'",
            (telegram_id,)
        ).fetchone()
    if not row:
        return False, "Сапоги не надеты.", gold
    item = EQUIPMENT_CATALOG.get(row["item_slug"], {})
    max_dur = item.get("durability", 100)
    if row["durability"] >= max_dur:
        return False, "Сапоги в отличном состоянии, ремонт не нужен.", gold
    cost = item.get("repair", 30)
    if gold < cost:
        return False, f"Нужно {cost}з для ремонта. У тебя {gold}з", gold
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_equipment SET durability=? WHERE telegram_id=? AND slot='boots'",
            (max_dur, telegram_id)
        )
        conn.commit()
    return True, f"✅ Сапоги отремонтированы! Прочность: {max_dur}/{max_dur}", gold - cost


def wear_boots(telegram_id: int, amount: int = 1):
    """Изнашивает сапоги при переходе."""
    _lazy()
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_equipment SET durability=MAX(0, durability-?) WHERE telegram_id=? AND slot='boots'",
            (amount, telegram_id)
        )
        conn.commit()


def get_equipment_bonuses(telegram_id: int) -> dict:
    """Возвращает суммарные бонусы от экипировки."""
    equipped = get_equipped(telegram_id)
    bonuses = {
        "crystal_slots": 0,
        "travel_speed": 0.0,   # доп. скидка на время пути (%)
        "buy_discount": 0.0,   # скидка на покупку (%)
        "sell_bonus": 0.0,     # надбавка при продаже (%)
        "energy_regen": 0.0,   # ускорение регенерации энергии (%)
        "boots_durability": 0,
        "boots_broken": False,
    }
    # Ремень
    belt = equipped.get("belt")
    if belt:
        bonuses["crystal_slots"] = belt.get("crystal_slots", 0)
    # Сапоги
    boots = equipped.get("boots")
    if boots:
        dur = boots.get("durability", 0)
        max_dur = boots.get("durability", 100)
        bonuses["boots_durability"] = dur
        if dur <= 0:
            bonuses["boots_broken"] = True
        else:
            # Бонус пропорционален прочности
            full_bonus = boots.get("travel_bonus", 0.0)
            bonuses["travel_speed"] = full_bonus * (dur / max(1, EQUIPMENT_CATALOG.get(boots["slug"], {}).get("durability", 100)))
    # Шляпа
    hat = equipped.get("hat")
    if hat:
        bonuses["buy_discount"] = hat.get("buy_discount", 0.0)
        bonuses["sell_bonus"] = hat.get("sell_bonus", 0.0)
    # Комбез
    suit = equipped.get("suit")
    if suit:
        bonuses["energy_regen"] = suit.get("energy_regen", 0.0)
    return bonuses


def render_equipment_panel(telegram_id: int) -> str:
    """Панель экипировки для показа игроку."""
    equipped = get_equipped(telegram_id)
    bonuses = get_equipment_bonuses(telegram_id)
    lines = ["⚔️ Экипировка персонажа\n"]
    for slot in SLOTS:
        slot_name = SLOT_NAMES[slot]
        item = equipped.get(slot)
        if item:
            dur_str = ""
            if slot == "boots":
                max_d = EQUIPMENT_CATALOG.get(item["slug"], {}).get("durability", 100)
                dur_pct = int(item["durability"] / max(1, max_d) * 100)
                bar = "█" * (dur_pct // 10) + "░" * (10 - dur_pct // 10)
                dur_str = f"\n    🔧 Прочность: [{bar}] {item['durability']}/{max_d}"
            lines.append(f"{slot_name}: {item['name']}\n    {item.get('desc','')}{dur_str}")
        else:
            lines.append(f"{slot_name}: — пусто")

    lines.append(f"\n📊 Бонусы:")
    if bonuses["crystal_slots"]:
        lines.append(f"  💎 Слотов для кристаллов: {bonuses['crystal_slots']}")
    if bonuses["travel_speed"]:
        lines.append(f"  🏃 Скорость перехода: +{int(bonuses['travel_speed']*100)}%")
    if bonuses["buy_discount"]:
        lines.append(f"  🛒 Скидка покупки: -{int(bonuses['buy_discount']*100)}%")
    if bonuses["sell_bonus"]:
        lines.append(f"  💰 Надбавка продажи: +{int(bonuses['sell_bonus']*100)}%")
    if bonuses["energy_regen"]:
        lines.append(f"  ⚡ Регенерация энергии: +{int(bonuses['energy_regen']*100)}%")

    return "\n".join(lines)
