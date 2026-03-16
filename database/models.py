from dataclasses import dataclass

@dataclass
class Player:
    telegram_id: int
    name: str
    location_slug: str = "dark_forest"
    current_region_slug: str = "valley_of_emotions"
    current_district_slug: str = "mushroom_path"
    gold: int = 120
    level: int = 1
    experience: int = 0
    energy: int = 12
    birth_cooldown_actions: int = 0

@dataclass
class Location:
    slug: str
    name: str
    mood: str
    biome: str
    description: str
