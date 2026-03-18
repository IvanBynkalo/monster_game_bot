from dataclasses import dataclass


@dataclass
class Player:
    telegram_id: int
    name: str
    location_slug: str = "silver_city"
    current_region_slug: str = "valley_of_emotions"
    current_district_slug: str = "market_square"
    gold: int = 120
    level: int = 1
    experience: int = 0
    energy: int = 12
    birth_cooldown_actions: int = 0
    strength: int = 1
    agility: int = 1
    intellect: int = 1
    stat_points: int = 0

    gatherer_level: int = 1
    gatherer_exp: int = 0

    hunter_level: int = 1
    hunter_exp: int = 0

    geologist_level: int = 1
    geologist_exp: int = 0

    alchemist_level: int = 1
    alchemist_exp: int = 0

    merchant_level: int = 1
    merchant_exp: int = 0

    bag_capacity: int = 12
    hp: int = 30
    max_hp: int = 30
    is_defeated: bool = False
    injury_turns: int = 0


@dataclass
class Location:
    slug: str
    name: str
    mood: str
    biome: str
    description: str
