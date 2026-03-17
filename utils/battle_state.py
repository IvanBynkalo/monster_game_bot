from typing import Dict, Any, Optional

_active_encounters: Dict[int, Dict[str, Any]] = {}


def start_encounter(user_id: int, encounter_data: Dict[str, Any]) -> None:
    _active_encounters[user_id] = encounter_data


def get_encounter(user_id: int) -> Optional[Dict[str, Any]]:
    return _active_encounters.get(user_id)


def is_in_encounter(user_id: int) -> bool:
    return user_id in _active_encounters


def update_encounter(user_id: int, encounter_data: Dict[str, Any]) -> None:
    _active_encounters[user_id] = encounter_data


def end_encounter(user_id: int) -> None:
    _active_encounters.pop(user_id, None)
