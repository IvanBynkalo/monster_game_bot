
from aiogram.types import Message
from database.repositories import get_player, get_player_codex
from game.codex_service import render_codex_list

ALL_MONSTERS = {}

def register_monster(name, rarity):
    ALL_MONSTERS[name] = {"rarity": rarity}

async def codex_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    discovered = get_player_codex(message.from_user.id)
    await message.answer(render_codex_list(discovered, ALL_MONSTERS))
