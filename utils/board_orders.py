from typing import Optional

_ACTIVE_BOARD_ORDERS: dict[int, dict] = {}


def get_active_board_order(user_id: int) -> Optional[dict]:
    return _ACTIVE_BOARD_ORDERS.get(user_id)


def set_active_board_order(user_id: int, order_data: dict) -> None:
    _ACTIVE_BOARD_ORDERS[user_id] = order_data


def clear_active_board_order(user_id: int) -> None:
    _ACTIVE_BOARD_ORDERS.pop(user_id, None)
