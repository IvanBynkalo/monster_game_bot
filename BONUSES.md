
# Система бонусов характеристик и навыков

## Сила героя (strength)
- +1 к атаке активного монстра за каждые 3 очка силы
- Применяется в: encounter_service.resolve_attack() → active_monster_attack += player.strength
- Код: bot.py fight_inline_callback строка: active_monster_attack=active.get("attack", 3) + player.strength

## Ловкость героя (agility)  
- Сокращает время перехода между локациями
- Каждые 5 очков = −10% времени пути, максимум −70%
- Применяется в: travel_service.get_travel_seconds()

## Интеллект героя (intellect)
- +1 к шансу поимки монстра за каждые 5 очков
- Применяется в: encounter_service.resolve_capture()

## Уровень Картографа (cartographer_level)
- Влияет на количество % исследования за одну вылазку
- Уровень 1-3:  +1% за вылазку
- Уровень 4-6:  +1-2% за вылазку  
- Уровень 7-10: +1-3% за вылазку
- Применяется в: grid_exploration_service.explore_cell()

## Навыки монстра → герой
Монстр может передавать бонусы через infection_type / комбо-мутации:

| Навык монстра | Тип | Бонус герою |
|---------------|-----|-------------|
| rage (Ярость) | ATK | +2-6 урона в бою |
| fear (Страх) | DEF | Контратака врага ×0.5 |
| instinct (Инстинкт) | CAP | +15% к поимке |
| inspiration (Вдохновение) | HEAL | +6 HP монстру + урон |

## Где применять силу к монстрам
В bot.py, fight_inline_callback, раздел "attack":
```python
active_monster_attack=active.get("attack", 3) + player.strength
```
Это уже реализовано — сила игрока добавляется к атаке монстра.

## Рекомендуемое расширение (пока не реализовано)
- Intellect: +1% поимки за 5 очков → в resolve_capture()
- Strength: +1 защита монстра за 4 очка силы → в mitigate_incoming_damage()
