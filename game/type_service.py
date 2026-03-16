TYPE_LABELS = {
    "flame": "🔥 Пламя",
    "shadow": "🌑 Тень",
    "nature": "🌿 Природа",
    "spirit": "👻 Дух",
    "bone": "💀 Кость",
    "storm": "⚡ Буря",
    "void": "🕳 Пустота",
    "echo": "🔊 Эхо",
}

TYPE_ADVANTAGES = {
    "flame": "nature",
    "nature": "bone",
    "bone": "spirit",
    "spirit": "shadow",
    "shadow": "echo",
    "echo": "void",
    "void": "storm",
    "storm": "flame",
}

def get_type_label(type_key: str | None):
    if not type_key:
        return "—"
    return TYPE_LABELS.get(type_key, type_key)

def get_damage_multiplier(attacker_type: str | None, defender_type: str | None) -> float:
    if not attacker_type or not defender_type:
        return 1.0
    if TYPE_ADVANTAGES.get(attacker_type) == defender_type:
        return 1.2
    if TYPE_ADVANTAGES.get(defender_type) == attacker_type:
        return 0.8
    return 1.0

def render_type_hint(attacker_type: str | None, defender_type: str | None) -> str:
    multiplier = get_damage_multiplier(attacker_type, defender_type)
    if multiplier > 1.0:
        return "Типовое преимущество: +20% урона"
    if multiplier < 1.0:
        return "Типовая слабость: -20% урона"
    return "Типы нейтральны"
