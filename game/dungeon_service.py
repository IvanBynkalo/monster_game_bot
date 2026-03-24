import random

from game.item_service import get_item

DUNGEONS = {
    "dark_forest": {
        "name": "🕳 Корни забытой чащи",
        "rooms": 5,
        "theme": "forest",
        "respawn_hours": 72,
        "boss": {
            "name": "🌲 Хозяин корней",
            "hp": 172,
            "attack": 13,
            "reward_gold": 185,
            "reward_exp": 34,
        },
    },
    "stone_hills": {
        "name": "🕳 Глубинная жила",
        "rooms": 5,
        "theme": "stone",
        "respawn_hours": 72,
        "boss": {
            "name": "⛰ Сердце монолита",
            "hp": 178,
            "attack": 14,
            "reward_gold": 192,
            "reward_exp": 36,
        },
    },
    "shadow_marsh": {
        "name": "🕳 Омут безмолвия",
        "rooms": 5,
        "theme": "marsh",
        "respawn_hours": 72,
        "boss": {
            "name": "🕸 Тёмный омутник",
            "hp": 176,
            "attack": 14,
            "reward_gold": 190,
            "reward_exp": 36,
        },
    },
}

THEME_TREASURES = {
    "forest": [
        {
            "gold": 44,
            "items": {"small_potion": 1},
            "text": "Ты находишь тайник под корнями и старый охотничий набор.",
        },
        {
            "gold": 58,
            "items": {"small_potion": 1, "basic_trap": 1},
            "text": "За треснувшей плитой скрыт схрон лесных следопытов.",
        },
    ],
    "stone": [
        {
            "gold": 36,
            "items": {"energy_capsule": 1},
            "text": "В нише скалы лежит запечатанный контейнер шахтёров.",
        },
        {
            "gold": 20,
            "items": {"small_potion": 1},
            "text": "Под обвалившейся колонной спрятан кошель и походный запас.",
        },
    ],
    "marsh": [
        {
            "gold": 15,
            "items": {"swamp_antidote": 1},
            "text": "В ржавом ларце лежит набор болотного путника.",
        },
        {
            "gold": 19,
            "items": {"small_potion": 1, "swamp_antidote": 1},
            "text": "Ты поднимаешь из грязи герметичный футляр с редкими припасами.",
        },
    ],
}

THEME_EVENTS = {
    "forest": [
        {
            "title": "🌿 Шепчущие корни",
            "text": "Живые корни сжимаются вокруг ног, но ты вырываешься и находишь жилу древней силы.",
            "reward_gold": 8,
            "reward_exp": 12,
        },
        {
            "title": "🪵 Забытый лагерь",
            "text": "Следы старого лагеря подсказывают безопасный путь вперёд.",
            "reward_gold": 10,
            "reward_exp": 10,
        },
    ],
    "stone": [
        {
            "title": "⛏ Рудная жила",
            "text": "Ты замечаешь прожилки ценной руды и собираешь часть добычи.",
            "reward_gold": 12,
            "reward_exp": 10,
        },
        {
            "title": "📜 Карта штрека",
            "text": "На стене высечены метки шахтёров. Они помогают избежать лишних тупиков.",
            "reward_gold": 8,
            "reward_exp": 12,
        },
    ],
    "marsh": [
        {
            "title": "🫧 Синий омут",
            "text": "Странный свет выводит тебя к древнему алтарю, где сохранились ценные вещи.",
            "reward_gold": 9,
            "reward_exp": 12,
        },
        {
            "title": "🪷 След болотника",
            "text": "Ты обходишь опасную трясину и находишь тайный проход.",
            "reward_gold": 11,
            "reward_exp": 10,
        },
    ],
}

CHOICE_EVENTS = {
    "forest": [
        {
            "title": "🌿 Сердце корней",
            "text": "Перед тобой живая сердцевина чащи. Она пульсирует силой и манит добычей.",
            "choices": [
                {
                    "id": "force",
                    "text": "⚔️ Прорваться силой",
                    "stat": "strength",
                    "base_chance": 0.50,
                    "success": {
                        "gold": 16,
                        "items": {"small_potion": 1},
                        "text": "Ты разрубаешь корни и добираешься до спрятанного тайника.",
                    },
                    "fail": {
                        "damage": 8,
                        "text": "Корни оплетают тебя и жалят острыми шипами.",
                    },
                },
                {
                    "id": "study",
                    "text": "🧠 Осмотреть осторожно",
                    "stat": "intellect",
                    "base_chance": 0.60,
                    "success": {
                        "exp": 14,
                        "text": "Ты замечаешь слабое место и обходишь опасность без лишнего шума.",
                    },
                    "fail": {
                        "damage": 4,
                        "text": "Ты почти справляешься, но задеваешь ловчий побег.",
                    },
                },
                {
                    "id": "leave",
                    "text": "🏃 Пройти мимо",
                    "stat": None,
                    "base_chance": 1.0,
                    "success": {
                        "text": "Ты решаешь не рисковать и идёшь дальше.",
                    },
                    "fail": {
                        "text": "Ты решаешь не рисковать и идёшь дальше.",
                    },
                },
            ],
        }
    ],
    "stone": [
        {
            "title": "⛏ Запечатанная шахта",
            "text": "Ты находишь старую дверь в штрек. За ней может быть добыча или обвал.",
            "choices": [
                {
                    "id": "break",
                    "text": "🔨 Вскрыть дверь",
                    "stat": "strength",
                    "base_chance": 0.70,
                    "success": {
                        "gold": 18,
                        "items": {"energy_capsule": 1},
                        "text": "Ты вскрываешь штрек и находишь запасы шахтёров.",
                    },
                    "fail": {
                        "damage": 7,
                        "text": "Дверь поддаётся, но сверху сыплются камни.",
                    },
                },
                {
                    "id": "inspect",
                    "text": "🧠 Проверить крепления",
                    "stat": "intellect",
                    "base_chance": 0.80,
                    "success": {
                        "exp": 14,
                        "text": "Ты находишь безопасный способ открыть проход и запоминаешь схему штрека.",
                    },
                    "fail": {
                        "damage": 4,
                        "text": "Один из крепежей трещит и ранит тебя осколками.",
                    },
                },
                {
                    "id": "skip",
                    "text": "🚶 Идти дальше",
                    "stat": None,
                    "base_chance": 1.0,
                    "success": {
                        "text": "Ты оставляешь сомнительный проход позади.",
                    },
                    "fail": {
                        "text": "Ты оставляешь сомнительный проход позади.",
                    },
                },
            ],
        }
    ],
    "marsh": [
        {
            "title": "🫧 Дышащий омут",
            "text": "В центре комнаты булькает вязкий омут. Внутри поблёскивает что-то ценное.",
            "choices": [
                {
                    "id": "grab",
                    "text": "🪝 Вытащить добычу",
                    "stat": "strength",
                    "base_chance": 0.68,
                    "success": {
                        "gold": 15,
                        "items": {"swamp_antidote": 1},
                        "text": "Ты подцепляешь добычу и быстро отходишь назад.",
                    },
                    "fail": {
                        "damage": 8,
                        "text": "Омут выплёвывает едкий пар и обжигает тебя.",
                    },
                },
                {
                    "id": "observe",
                    "text": "👀 Выждать момент",
                    "stat": "intellect",
                    "base_chance": 0.80,
                    "success": {
                        "exp": 13,
                        "text": "Ты замечаешь ритм всплесков и проходишь безопаснее.",
                    },
                    "fail": {
                        "damage": 4,
                        "text": "Ты затягиваешь паузу и ловишь всплеск ядовитой жижи.",
                    },
                },
                {
                    "id": "retreat",
                    "text": "🏃 Не рисковать",
                    "stat": None,
                    "base_chance": 1.0,
                    "success": {
                        "text": "Ты решаешь не испытывать судьбу.",
                    },
                    "fail": {
                        "text": "Ты решаешь не испытывать судьбу.",
                    },
                },
            ],
        }
    ],
}

THEME_TRAPS = {
    "forest": [
        {"title": "🪤 Колючий проход", "text": "Из стен выстреливают шипастые лозы.", "damage": 8},
        {"title": "🍂 Ложная тропа", "text": "Под ковром листьев скрыта яма с корнями.", "damage": 10},
    ],
    "stone": [
        {"title": "🪨 Каменный обвал", "text": "С потолка срываются острые осколки.", "damage": 9},
        {"title": "⚙ Древний механизм", "text": "Старый шахтный капкан срабатывает у тебя под ногами.", "damage": 11},
    ],
    "marsh": [
        {"title": "☣ Ядовитый пар", "text": "Из трещин поднимается едкий болотный туман.", "damage": 8},
        {"title": "🫙 Скользкий уступ", "text": "Ты срываешься на вязкую глину и едва удерживаешься.", "damage": 10},
    ],
}

ENEMIES = {
    "forest": {
        "combat": [
            ("Корневой хищник", 32, 8, 20, 11),
            ("Чащобный зверь", 35, 9, 22, 12),
        ],
        "elite": [
            ("Сторож дубравы", 46, 11, 34, 18),
            ("Лозовый палач", 48, 12, 36, 18),
        ],
    },
    "stone": {
        "combat": [
            ("Каменный бур", 34, 9, 22, 12),
            ("Пещерный ломатель", 36, 10, 24, 12),
        ],
        "elite": [
            ("Хранитель жилы", 48, 12, 36, 18),
            ("Пыльный титанок", 50, 12, 38, 19),
        ],
    },
    "marsh": {
        "combat": [
            ("Болотный пастух", 33, 9, 21, 12),
            ("Смоляной охотник", 36, 10, 24, 13),
        ],
        "elite": [
            ("Трясинный страж", 47, 12, 35, 18),
            ("Чёрный омутник", 49, 12, 37, 19),
        ],
    },
}


def get_dungeon(location_slug: str):
    data = DUNGEONS.get(location_slug)
    return data.copy() if data else None


def _build_room_plan(rooms_total: int) -> list[str]:
    plan = ["combat"]
    pool = [
        "combat",
        "combat",
        "treasure",
        "trap",
        "event",
        "event_choice",
        "elite",
        "rest",
    ]
    treasure_count = 0
    rest_count = 0
    choice_count = 0

    while len(plan) < rooms_total - 1:
        candidates = []
        for room_type in pool:
            if room_type == plan[-1]:
                continue
            if room_type == "treasure" and treasure_count >= 1:
                continue
            if room_type == "rest" and rest_count >= 1:
                continue
            if room_type == "event_choice" and choice_count >= 1:
                continue
            candidates.append(room_type)

        if len(plan) >= rooms_total - 2:
            weighted = [r for r in candidates if r in {"combat", "elite", "trap", "event", "event_choice"}] or candidates
        else:
            weighted = candidates

        room_type = random.choice(weighted)
        plan.append(room_type)

        if room_type == "treasure":
            treasure_count += 1
        elif room_type == "rest":
            rest_count += 1
        elif room_type == "event_choice":
            choice_count += 1

    plan.append("boss")
    return plan


def start_dungeon_state(location_slug: str):
    dungeon = get_dungeon(location_slug)
    if not dungeon:
        return None

    rooms_total = dungeon["rooms"]
    return {
        "location_slug": location_slug,
        "name": dungeon["name"],
        "theme": dungeon["theme"],
        "room_index": 0,
        "rooms_total": rooms_total,
        "room_plan": _build_room_plan(rooms_total),
        "boss": dungeon["boss"].copy(),
        "current_room": None,
        "completed": False,
        "summary": {
            "gold": 0,
            "exp": 0,
            "items": {},
            "rooms_cleared": 0,
            "enemies_defeated": 0,
            "traps_triggered": 0,
        },
    }


def _build_enemy(theme: str, tier: str) -> dict:
    name, hp, attack, reward_gold, reward_exp = random.choice(ENEMIES[theme][tier])
    return {
        "name": name,
        "hp": hp,
        "attack": attack,
        "reward_gold": reward_gold,
        "reward_exp": reward_exp,
    }


def generate_room(state: dict):
    next_index = state["room_index"]
    room_type = state["room_plan"][next_index]
    theme = state["theme"]

    if room_type == "boss":
        return {
            "type": "boss",
            "title": "👑 Зал босса",
            "text": f"Ты входишь в последний зал. Здесь тебя ждёт {state['boss']['name']}.",
            "enemy": state["boss"].copy(),
        }

    if room_type == "combat":
        enemy = _build_enemy(theme, "combat")
        return {
            "type": "combat",
            "title": "⚔️ Враждебная комната",
            "text": f"Из мрака выходит {enemy['name']}. Без боя дальше не пройти.",
            "enemy": enemy,
        }

    if room_type == "elite":
        enemy = _build_enemy(theme, "elite")
        return {
            "type": "elite",
            "title": "💀 Опасный зал",
            "text": f"Воздух густеет. Перед тобой появляется элитный враг — {enemy['name']}.",
            "enemy": enemy,
        }

    if room_type == "treasure":
        treasure = random.choice(THEME_TREASURES[theme])
        return {
            "type": "treasure",
            "title": "🏺 Тайник",
            "text": treasure["text"],
            "gold": treasure["gold"],
            "items": treasure["items"].copy(),
        }

    if room_type == "rest":
        return {
            "type": "rest",
            "title": "⛲ Тихий привал",
            "text": "Ты находишь безопасный угол и можешь перевести дух перед следующим рывком.",
            "heal": 12,
            "energy": 1,
        }

    if room_type == "trap":
        trap = random.choice(THEME_TRAPS[theme])
        return {
            "type": "trap",
            "title": trap["title"],
            "text": trap["text"],
            "damage": trap["damage"],
        }

    if room_type == "event_choice":
        event = random.choice(CHOICE_EVENTS[theme])
        return {
            "type": "event_choice",
            "title": event["title"],
            "text": event["text"],
            "choices": event["choices"],
        }

    event = random.choice(THEME_EVENTS[theme])
    return {
        "type": "event",
        "title": event["title"],
        "text": event["text"],
        "reward_gold": event["reward_gold"],
        "reward_exp": event["reward_exp"],
    }


def render_item_rewards(items: dict) -> str:
    if not items:
        return "• Нет предметов"

    lines = []
    for slug, amount in items.items():
        item = get_item(slug)
        if item:
            lines.append(f"• {item['emoji']} {item['name']} x{amount}")
        else:
            lines.append(f"• {slug} x{amount}")
    return "\n".join(lines)


def render_dungeon_summary(state: dict) -> str:
    summary = state.get("summary", {})
    items_text = render_item_rewards(summary.get("items", {}))
    return (
        "🏁 Поход завершён!\n\n"
        f"🗺 Комнат пройдено: {summary.get('rooms_cleared', 0)} / {state.get('rooms_total', 0)}\n"
        f"⚔️ Побеждено врагов: {summary.get('enemies_defeated', 0)}\n"
        f"🪤 Ловушек пережито: {summary.get('traps_triggered', 0)}\n"
        f"💰 Золото: +{summary.get('gold', 0)}\n"
        f"✨ Опыт: +{summary.get('exp', 0)}\n\n"
        f"🎒 Добыча:\n{items_text}"
    )


def render_dungeon_state(state: dict):
    room = state.get("current_room")
    lines = [
        f"{state['name']}",
        "",
        f"Комната: {state['room_index']} / {state['rooms_total']}",
    ]

    if room:
        lines.extend(["", room["title"], room["text"]])

        if room["type"] == "event_choice":
            lines.extend(["", "Что будешь делать?"])

        if room["type"] in {"combat", "elite", "boss"}:
            danger = "🔥 Сильный противник" if room["type"] == "elite" else ""
            if danger:
                lines.append(danger)
            lines.append(
                f"Враг: {room['enemy']['name']} | HP: {room['enemy']['hp']} | Атака: {room['enemy']['attack']}"
            )
    else:
        lines.append("")
        lines.append("Подземелье замерло. Решай, что делать дальше.")

    return "\n".join(lines)
