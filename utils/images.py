"""
utils/images.py — централизованное управление изображениями.

Вся логика работы с картинками в одном месте.
Если файл не найден — отправляем текст без фото (graceful fallback).
"""
from pathlib import Path
from aiogram.types import FSInputFile, Message

ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"

# ── Пути по категориям ────────────────────────────────────────────────────────
CITY_DIR      = ASSETS_ROOT / "city"
LOCATION_DIR  = ASSETS_ROOT / "locations"
MONSTER_DIR   = ASSETS_ROOT / "monsters"
EMOTION_DIR   = ASSETS_ROOT / "emotions"
DUNGEON_DIR   = ASSETS_ROOT / "dungeons"

# ── Маппинги ──────────────────────────────────────────────────────────────────

# Город: контекст → файл
CITY_IMAGES: dict[str, str] = {
    "city_square":    "city_square.png",
    "market_square":  "city_square.png",
    "craft_quarter":  "alchemy_lab.png",
    "guild_quarter":  "guild_hall.png",
    "main_gate":      "city_gate.png",
    "hunters_guild":  "hunters_guild.png",
    "bort":           "bort_shop.png",
    "mirna":          "mirna_shop.png",
    "varg":           "varg_shop.png",
    "bags":           "bag_market.png",
    "board":          "city_board.png",
    "traps":          "trap_workshop.png",
}

# Локации: slug → файл
LOCATION_IMAGES: dict[str, str] = {
    "silver_city":    "silver_city.png",
    "dark_forest":    "dark_forest.png",
    "emerald_fields": "emerald_fields.png",
    "stone_hills":    "stone_hills.png",
    "shadow_marsh":   "shadow_marsh.png",
    "shadow_swamp":   "shadow_swamp.png",
    "ancient_ruins":  "ancient_ruins.png",
    "bone_desert":    "bone_desert.png",
    "volcano_wrath":  "volcano_wrath.png",
    "storm_ridge":    "storm_ridge.png",
    "emotion_rift":   "emotion_rift.png",
}

# Типы монстров: monster_type → файл
MONSTER_TYPE_IMAGES: dict[str, str] = {
    "nature":  "monster_nature.png",
    "shadow":  "monster_shadow.png",
    "flame":   "monster_flame.png",
    "bone":    "monster_bone.png",
    "storm":   "monster_storm.png",
    "echo":    "monster_echo.png",
    "spirit":  "monster_spirit.png",
    "void":    "monster_void.png",
}

# Эмоциональные рождения: emotion → файл
BIRTH_IMAGES: dict[str, str] = {
    "rage":        "birth_rage.png",
    "fear":        "birth_fear.png",
    "instinct":    "birth_instinct.png",
    "inspiration": "birth_inspiration.png",
    "sadness":     "birth_sadness.png",
    "joy":         "birth_joy.png",
    "disgust":     "birth_disgust.png",
    "surprise":    "birth_surprise.png",
}

# Подземелья: location_slug → файл
DUNGEON_IMAGES: dict[str, str] = {
    "dark_forest":   "dungeon_forest.png",
    "stone_hills":   "dungeon_stone.png",
    "shadow_marsh":  "dungeon_marsh.png",
}


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


async def send_location_image(message: Message, location_slug: str, caption: str, reply_markup=None):
    """Картинка локации при переходе или карте."""
    filename = LOCATION_IMAGES.get(location_slug)
    path = (LOCATION_DIR / filename) if filename else None
    await send_image(message, path, caption, reply_markup)


async def send_monster_image(message: Message, monster_type: str, caption: str, reply_markup=None):
    """Картинка типа монстра при встрече или в профиле монстра."""
    filename = MONSTER_TYPE_IMAGES.get(monster_type)
    path = (MONSTER_DIR / filename) if filename else None
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
