PROFESSION_LEVEL_CAP = 10

PROFESSION_FIELD_MAP = {
    "gatherer": ("gatherer_level", "gatherer_exp"),
    "hunter": ("hunter_level", "hunter_exp"),
    "geologist": ("geologist_level", "geologist_exp"),
    "alchemist": ("alchemist_level", "alchemist_exp"),
    "merchant": ("merchant_level", "merchant_exp"),
}


def get_profession_exp_required(level: int) -> int:
    # Сколько XP нужно, чтобы перейти с текущего уровня на следующий
    # 1->2: 10, 2->3: 14, 3->4: 18 ...
    return 6 + level * 4


def get_profession_state(player, kind: str):
    fields = PROFESSION_FIELD_MAP.get(kind)
    if not fields:
        return None

    level_field, exp_field = fields
    level = getattr(player, level_field, 1)
    exp = getattr(player, exp_field, 0)

    return {
        "kind": kind,
        "level_field": level_field,
        "exp_field": exp_field,
        "level": level,
        "exp": exp,
        "exp_to_next": 0 if level >= PROFESSION_LEVEL_CAP else get_profession_exp_required(level),
    }


def improve_profession_from_action(telegram_id: int, kind: str, amount: int = 1):
    player = get_player(telegram_id)
    if not player:
        return None

    fields = PROFESSION_FIELD_MAP.get(kind)
    if not fields:
        return None

    level_field, exp_field = fields

    old_level = getattr(player, level_field, 1)
    old_exp = getattr(player, exp_field, 0)

    if old_level >= PROFESSION_LEVEL_CAP:
        return {
            "kind": kind,
            "leveled_up": False,
            "level_before": old_level,
            "level_after": old_level,
            "exp_before": old_exp,
            "exp_after": old_exp,
            "exp_to_next": 0,
            "is_max_level": True,
            "gained_exp": 0,
        }

    new_exp = old_exp + max(0, amount)
    new_level = old_level
    leveled_up = False

    while new_level < PROFESSION_LEVEL_CAP:
        need = get_profession_exp_required(new_level)
        if new_exp < need:
            break
        new_exp -= need
        new_level += 1
        leveled_up = True

    if new_level >= PROFESSION_LEVEL_CAP:
        new_level = PROFESSION_LEVEL_CAP
        new_exp = 0

    setattr(player, level_field, new_level)
    setattr(player, exp_field, new_exp)

    return {
        "kind": kind,
        "leveled_up": leveled_up,
        "level_before": old_level,
        "level_after": new_level,
        "exp_before": old_exp,
        "exp_after": new_exp,
        "exp_to_next": 0 if new_level >= PROFESSION_LEVEL_CAP else get_profession_exp_required(new_level),
        "is_max_level": new_level >= PROFESSION_LEVEL_CAP,
        "gained_exp": max(0, amount),
    }
