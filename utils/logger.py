from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "game.log"

def log_event(event_type: str, telegram_id: int | None = None, details: str = ""):
    timestamp = datetime.utcnow().isoformat()
    line = f"[{timestamp}] {event_type}"
    if telegram_id is not None:
        line += f" user={telegram_id}"
    if details:
        line += f" | {details}"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
