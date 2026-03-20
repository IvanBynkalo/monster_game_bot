"""
Аналитика и метрики (рекомендация #20).
Логирует события, предоставляет сводки для балансировки.
"""
import logging
from database.repositories import track as _track, get_analytics_summary

logger = logging.getLogger(__name__)

# ── Типизированные события ────────────────────────────────────────────────────

def track_new_player(telegram_id: int, name: str):
    _track(telegram_id, "new_player", {"name": name})

def track_battle_win(telegram_id: int, monster_name: str, rarity: str, location: str):
    _track(telegram_id, "battle_win", {"monster": monster_name, "rarity": rarity, "location": location})

def track_capture(telegram_id: int, monster_name: str, rarity: str):
    _track(telegram_id, "capture", {"monster": monster_name, "rarity": rarity})

def track_explore(telegram_id: int, location: str):
    _track(telegram_id, "explore", {"location": location})

def track_craft(telegram_id: int, recipe: str):
    _track(telegram_id, "craft", {"recipe": recipe})

def track_gather(telegram_id: int, resource: str, location: str):
    _track(telegram_id, "gather", {"resource": resource, "location": location})

def track_level_up(telegram_id: int, new_level: int):
    _track(telegram_id, "level_up", {"level": new_level})

def track_emotion_birth(telegram_id: int, monster_name: str, emotion: str, rarity: str):
    _track(telegram_id, "emotion_birth", {"monster": monster_name, "emotion": emotion, "rarity": rarity})

def track_combo_mutation(telegram_id: int, combo_name: str, emotions: list):
    _track(telegram_id, "combo_mutation", {"combo": combo_name, "emotions": emotions})

def track_evolution(telegram_id: int, old_name: str, new_name: str):
    _track(telegram_id, "evolution", {"from": old_name, "to": new_name})

def track_pvp(telegram_id: int, opponent_id: int, won: bool):
    _track(telegram_id, "pvp", {"opponent": opponent_id, "won": won})

def track_dungeon_complete(telegram_id: int, dungeon_name: str, boss_killed: bool):
    _track(telegram_id, "dungeon_complete", {"dungeon": dungeon_name, "boss": boss_killed})

def track_location_change(telegram_id: int, from_loc: str, to_loc: str):
    _track(telegram_id, "location_change", {"from": from_loc, "to": to_loc})

def track_shop_purchase(telegram_id: int, item: str, price: int, currency: str = "gold"):
    _track(telegram_id, "shop_purchase", {"item": item, "price": price, "currency": currency})

def track_player_defeated(telegram_id: int, location: str):
    _track(telegram_id, "player_defeated", {"location": location})

def track_session_start(telegram_id: int):
    _track(telegram_id, "session_start", {})


# ── Форматирование отчёта для админа ─────────────────────────────────────────

def render_analytics_report() -> str:
    summary = get_analytics_summary()
    lines = [
        "📊 Аналитика игры\n",
        f"Всего игроков:  {summary['total_players']}",
        f"Активных (7д):  {summary['active_7d']}",
        "",
        "Топ событий:",
    ]
    for ev in summary["top_events"][:15]:
        lines.append(f"  {ev['event']:30s} {ev['cnt']:>6}")
    return "\n".join(lines)
