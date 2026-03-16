from game.location_rules import is_city
from game.district_service import get_district_name

CITY_BUILDINGS = {
    "market_square": [
        "🏪 Торговая лавка",
        "🎒 Лавка сумок",
        "🐲 Рынок монстров",
        "💰 Скупщик ресурсов",
        "📜 Доска заказов",
    ],
    "craft_quarter": [
        "⚗ Алхимическая лаборатория",
        "🪤 Мастер ловушек",
    ],
    "guild_quarter": [
        "🎯 Гильдия ловцов",
        "🌿 Гильдия собирателей",
        "⛏ Гильдия геологов",
        "⚗ Гильдия алхимиков",
    ],
    "main_gate": [
        "🚶 Покинуть город",
        "🛡 Городская стража",
    ],
}

CITY_BOARD_QUESTS = [
    {
        "id": "city_board_herbs",
        "title": "Заказ травника",
        "description": "Продай 3 🌿 Лесная трава скупщику ресурсов.",
        "type": "sell_resource",
        "resource": "forest_herb",
        "target": 3,
        "reward_gold": 35,
        "reward_exp": 12,
    },
    {
        "id": "city_board_stones",
        "title": "Нужна руда для печей",
        "description": "Продай 2 🔥 Угольный камень.",
        "type": "sell_resource",
        "resource": "ember_stone",
        "target": 2,
        "reward_gold": 40,
        "reward_exp": 14,
    },
]

GUILD_QUESTS = [
    {
        "id": "guild_hunters_first",
        "title": "Испытание ловца",
        "description": "Поймай 1 монстра после посещения гильдии ловцов.",
        "type": "capture",
        "target": 1,
        "reward_gold": 30,
        "reward_exp": 12,
        "profession": "hunter",
    },
    {
        "id": "guild_gatherers_first",
        "title": "Испытание собирателя",
        "description": "Собери 4 обычных ресурса.",
        "type": "gather",
        "target": 4,
        "reward_gold": 30,
        "reward_exp": 12,
        "profession": "gatherer",
    },
    {
        "id": "guild_geology_first",
        "title": "Испытание геолога",
        "description": "Добудь 2 каменных ресурса.",
        "type": "geology",
        "target": 2,
        "reward_gold": 35,
        "reward_exp": 14,
        "profession": "geologist",
    },
    {
        "id": "guild_alchemy_first",
        "title": "Испытание алхимика",
        "description": "Создай 2 предмета в лаборатории.",
        "type": "craft_any",
        "target": 2,
        "reward_gold": 40,
        "reward_exp": 16,
        "profession": "alchemist",
    },
]

def render_city_menu(player) -> str:
    if not is_city(player.location_slug):
        return "Ты сейчас не в городе."
    district_name = get_district_name(player.location_slug, player.current_district_slug)
    buildings = CITY_BUILDINGS.get(player.current_district_slug, [])
    lines = [
        "🏙 Сереброград",
        "",
        f"Текущий район: {district_name}",
        "",
        "Доступные здания и действия:",
    ]
    for b in buildings:
        lines.append(f"• {b}")
    return "\n".join(lines)

def render_city_board() -> str:
    lines = ["📜 Доска заказов", ""]
    for quest in CITY_BOARD_QUESTS:
        lines.extend([
            f"{quest['title']}",
            quest["description"],
            f"Награда: {quest['reward_gold']} золота, {quest['reward_exp']} опыта",
            "",
        ])
    return "\n".join(lines)

def render_guild_text(guild_name: str, description: str, quests: list[dict]) -> str:
    lines = [guild_name, "", description, "", "Доступные поручения:"]
    for quest in quests:
        lines.extend([
            f"— {quest['title']}",
            quest["description"],
            f"Награда: {quest['reward_gold']} золота, {quest['reward_exp']} опыта",
            "",
        ])
    return "\n".join(lines)
