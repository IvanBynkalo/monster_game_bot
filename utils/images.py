"""
utils/images.py — централизованное управление изображениями.

Вся логика работы с картинками в одном месте.
Если файл не найден — отправляем текст без фото (graceful fallback).
"""
from pathlib import Path
from aiogram.types import FSInputFile, Message
import re

ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"

# ── Пути по категориям ────────────────────────────────────────────────────────
CITY_DIR = ASSETS_ROOT / "city"
LOCATION_DIR = ASSETS_ROOT / "locations"
MONSTER_DIR = ASSETS_ROOT / "monsters"
EMOTION_DIR = ASSETS_ROOT / "emotions"
DUNGEON_DIR = ASSETS_ROOT / "dungeons"

# ── Маппинги ──────────────────────────────────────────────────────────────────

# Город: контекст → файл
CITY_IMAGES: dict[str, str] = {
    "city_square": "city_square.png",
    "market_square": "city_square.png",
    "craft_quarter": "alchemy_lab.png",
    "guild_quarter": "guild_hall.png",
    "main_gate": "city_gate.png",
    "hunters_guild": "hunters_guild.png",
    "bort": "bort_shop.png",
    "mirna": "mirna_shop.png",
    "varg": "varg_shop.png",
    "bags": "bag_market.png",
    "board": "city_board.png",
    "traps": "trap_workshop.png",
}

# Локации: slug → файл
LOCATION_IMAGES: dict[str, str] = {
    "silver_city": "silver_city.png",
    "dark_forest": "dark_forest.png",
    "emerald_fields": "emerald_fields.png",
    "stone_hills": "stone_hills.png",
    "shadow_marsh": "shadow_marsh.png",
    "shadow_swamp": "shadow_swamp.png",
    "ancient_ruins": "ancient_ruins.png",
    "bone_desert": "bone_desert.png",
    "volcano_wrath": "volcano_wrath.png",
    "storm_ridge": "storm_ridge.png",
    "emotion_rift": "emotion_rift.png",
}

# Картинки районов: district_slug → файл в assets/locations/districts/
# Добавь файлы в assets/locations/districts/ — бот подхватит автоматически
DISTRICT_IMAGES: dict[str, str] = {
    # Изумрудные поля
    "green_meadow":   "district_green_meadow.png",
    "flower_valley":  "district_flower_valley.png",
    # Каменные холмы
    "old_mine":       "district_old_mine.png",
    "rock_pass":      "district_rock_pass.png",
    # Болота теней
    "fog_pool":       "district_fog_pool.png",
    "sunken_ruins":   "district_sunken_ruins.png",
    # Тёмный лес
    "mushroom_path":  "district_mushroom_path.png",
    "wet_thicket":    "district_wet_thicket.png",
    "whisper_den":    "district_whisper_den.png",
    # Болота (доп.)
    "black_water":    "district_black_water.png",
    "fog_trail":      "district_fog_trail.png",
    "grave_of_voices":"district_grave_of_voices.png",
    # Вулкан
    "ash_slope":      "district_ash_slope.png",
    "lava_bridge":    "district_lava_bridge.png",
    "heart_of_magma": "district_heart_of_magma.png",
}

DISTRICT_DIR = LOCATION_DIR / "districts"

# Типы монстров: monster_type → файл
MONSTER_TYPE_IMAGES: dict[str, str] = {
    "nature": "monster_nature.png",
    "shadow": "monster_shadow.png",
    "flame": "monster_flame.png",
    "bone": "monster_bone.png",
    "storm": "monster_storm.png",
    "echo": "monster_echo.png",
    "spirit": "monster_spirit.png",
    "void": "monster_void.png",
}

# Эмоциональные рождения: emotion → файл
BIRTH_IMAGES: dict[str, str] = {
    "rage": "birth_rage.png",
    "fear": "birth_fear.png",
    "instinct": "birth_instinct.png",
    "inspiration": "birth_inspiration.png",
    "sadness": "birth_sadness.png",
    "joy": "birth_joy.png",
    "disgust": "birth_disgust.png",
    "surprise": "birth_surprise.png",
}

# Подземелья: location_slug → файл
DUNGEON_IMAGES: dict[str, str] = {
    "dark_forest": "dungeon_forest.png",
    "stone_hills": "dungeon_stone.png",
    "shadow_marsh": "dungeon_marsh.png",
}

# Уникальные картинки зверей / существ:
# ключ = code/slug, значение = файл в assets/monsters
MONSTER_NAME_IMAGES: dict[str, str] = {
    "fox_forest": "fox_forest.png",
    "wolf_forest": "wolf_forest.png",
    "wolf_alpha": "wolf_alpha.png",
    "bear_brown": "bear_brown.png",
    "giant_forest": "giant_forest.png",
    "mouse_field": "mouse_field.png",
    "rabbit_field": "rabbit_field.png",
    "deer_horned": "deer_horned.png",
    "bull_steppe": "bull_steppe.png",
    "eagle_gold": "eagle_gold.png",
    "groundhog_mountain": "groundhog_mountain.png",
    "lizard_stone": "lizard_stone.png",
    "goat_mountain": "goat_mountain.png",
    "boar_rock": "boar_rock.png",
    "lion_mountain": "lion_mountain.png",
    "frog_swamp": "frog_swamp.png",
    "rat_swamp": "rat_swamp.png",
    "snake_swamp": "snake_swamp.png",
    "boar_swamp": "boar_swamp.png",
    "crocodile_swamp": "crocodile_swamp.png",
    "snake_mud": "snake_mud.png",
    "otter_dark": "otter_dark.png",
    "varan_swamp": "varan_swamp.png",
    "lizard_ash": "lizard_ash.png",
    "crab_lava": "crab_lava.png",
    "salamander_fire": "salamander_fire.png",
    "wolf_volcano": "wolf_volcano.png",
    "boar_magma": "boar_magma.png",
    "rabbit_wind": "rabbit_wind.png",
    "fox_flower": "fox_flower.png",
    "deer_golden_horn": "deer_golden_horn.png",
    "beast_granite": "beast_granite.png",
    "alpha_thicket": "alpha_thicket.png",
    "hunter_bog": "hunter_bog.png",
    "crimson_stalker": "crimson_stalker.png",
    "storm_phantom": "storm_phantom.png",
    "bone_wanderer": "bone_wanderer.png",
    "forest_guardian": "forest_guardian.png",
    "stone_colossus": "stone_colossus.png",
    "marsh_king": "marsh_king.png",
    "root_master": "root_master.png",
    "monolith_heart": "monolith_heart.png",
    "dark_deep_dweller": "dark_deep_dweller.png",
}

# Привязка игрового имени к стабильному коду картинки
MONSTER_NAME_TO_CODE: dict[str, str] = {
    "Лесная лисица": "fox_forest",
    "Лесной волк": "wolf_forest",
    "Матёрый волк": "wolf_alpha",
    "Бурый медведь": "bear_brown",
    "Лесной великан": "giant_forest",
    "Полевая мышь": "mouse_field",
    "Луговой заяц": "rabbit_field",
    "Рогатый олень": "deer_horned",
    "Степной тур": "bull_steppe",
    "Золотой орёл": "eagle_gold",
    "Горный суслик": "groundhog_mountain",
    "Каменная ящерица": "lizard_stone",
    "Горный козёл": "goat_mountain",
    "Скальный кабан": "boar_rock",
    "Горный лев": "lion_mountain",
    "Болотная жаба": "frog_swamp",
    "Топяная крыса": "rat_swamp",
    "Болотная змея": "snake_swamp",
    "Топяной кабан": "boar_swamp",
    "Болотный крокодил": "crocodile_swamp",
    "Иловый уж": "snake_mud",
    "Тёмная выдра": "otter_dark",
    "Болотный варан": "varan_swamp",
    "Пепельная ящерица": "lizard_ash",
    "Лавовый краб": "crab_lava",
    "Огненная саламандра": "salamander_fire",
    "Вулканический волк": "wolf_volcano",
    "Магматический кабан": "boar_magma",
    "Ветряной заяц": "rabbit_wind",
    "Лепестковый лис": "fox_flower",
    "Златорогий олень": "deer_golden_horn",
    "Гранитный зверь": "beast_granite",
    "Чащобный альфа": "alpha_thicket",
    "Топный ловчий": "hunter_bog",
    "Багровый Следопыт": "crimson_stalker",
    "Грозовой Фантом": "storm_phantom",
    "Костяной Странник": "bone_wanderer",
    "🌲 Древний страж леса": "forest_guardian",
    "⛰ Колосс камня": "stone_colossus",
    "🕸 Повелитель болот": "marsh_king",
    "🌲 Хозяин корней": "root_master",
    "⛰ Сердце монолита": "monolith_heart",
    "🕸 Тёмный омутник": "dark_deep_dweller",
}


# ── Вспомогательные функции ──────────────────────────────────────────────────

def _existing(path: Path | None) -> Path | None:
    if path and path.exists():
        return path
    return None


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()

    ru_map = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
        "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
        "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
        "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
        "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
        "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
        "э": "e", "ю": "yu", "я": "ya",
    }

    value = "".join(ru_map.get(ch, ch) for ch in value)
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def get_monster_image_path(monster_name: str | None = None, monster_type: str | None = None) -> Path | None:
    """
    Ищет картинку монстра/зверя по имени, а если не находит — по типу.
    Приоритет:
    1. Прямой маппинг MONSTER_NAME_TO_CODE -> MONSTER_NAME_IMAGES
    2. Авто slug по имени -> <slug>.png
    3. Картинка по monster_type
    4. monster_default.png
    """
    if monster_name:
        code = MONSTER_NAME_TO_CODE.get(monster_name)
        if code:
            filename = MONSTER_NAME_IMAGES.get(code)
            path = _existing(MONSTER_DIR / filename) if filename else None
            if path:
                return path

        slug = _slugify(monster_name)
        direct = _existing(MONSTER_DIR / f"{slug}.png")
        if direct:
            return direct

    if monster_type:
        filename = MONSTER_TYPE_IMAGES.get(monster_type)
        path = _existing(MONSTER_DIR / filename) if filename else None
        if path:
            return path

    return _existing(MONSTER_DIR / "monster_default.png")


# ── Основная функция отправки ─────────────────────────────────────────────────

async def send_image(
    message: Message,
    image_path: Path | None,
    caption: str,
    reply_markup=None,
    parse_mode: str | None = None,
) -> None:
    """
    Отправляет фото с подписью. Если файл не найден — отправляет текст.
    Использовать везде вместо прямого message.answer_photo().
    """
    if image_path and image_path.exists():
        await message.answer_photo(
            photo=FSInputFile(str(image_path)),
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    else:
        await message.answer(caption, reply_markup=reply_markup, parse_mode=parse_mode)


# ── Хелперы по контексту ─────────────────────────────────────────────────────

async def send_city_image(message: Message, context: str, caption: str, reply_markup=None):
    """Картинка для городского экрана. context = ключ из CITY_IMAGES."""
    filename = CITY_IMAGES.get(context, "city_square.png")
    await send_image(message, CITY_DIR / filename, caption, reply_markup)


async def send_location_image(
    message: Message,
    location_slug: str,
    caption: str,
    reply_markup=None,
    district_slug: str | None = None,
):
    """
    Картинка локации при переходе или карте.
    Если передан district_slug и для него есть картинка — показывает её.
    Иначе fallback на картинку локации.
    """
    # Сначала пробуем картинку района
    if district_slug:
        district_filename = DISTRICT_IMAGES.get(district_slug)
        district_path = (DISTRICT_DIR / district_filename) if district_filename else None
        if district_path and district_path.exists():
            await send_image(message, district_path, caption, reply_markup)
            return

    # Fallback на картинку локации
    filename = LOCATION_IMAGES.get(location_slug)
    path = (LOCATION_DIR / filename) if filename else None
    await send_image(message, path, caption, reply_markup)


async def send_monster_image(message: Message, monster_type: str, caption: str, reply_markup=None):
    """Старый совместимый вариант: картинка только по типу."""
    filename = MONSTER_TYPE_IMAGES.get(monster_type)
    path = (MONSTER_DIR / filename) if filename else None
    await send_image(message, path, caption, reply_markup)


async def send_monster_card_image(
    message: Message,
    monster_name: str | None,
    monster_type: str | None,
    caption: str,
    reply_markup=None,
):
    """
    Новый вариант: сначала ищет уникальную картинку зверя/монстра по имени,
    затем fallback по типу.
    """
    path = get_monster_image_path(monster_name=monster_name, monster_type=monster_type)
    await send_image(message, path, caption, reply_markup)


async def send_birth_image(message: Message, emotion: str, caption: str, reply_markup=None):
    """Картинка при эмоциональном рождении монстра."""
    filename = BIRTH_IMAGES.get(emotion)
    path = (EMOTION_DIR / filename) if filename else None
    await send_image(message, path, caption, reply_markup)


async def send_dungeon_image(message: Message, location_slug: str, caption: str, reply_markup=None):
    """Картинка при входе в подземелье."""
    filename = DUNGEON_IMAGES.get(location_slug)
    path = (DUNGEON_DIR / filename) if filename else None
    await send_image(message, path, caption, reply_markup)
