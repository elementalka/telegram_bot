import json
from pathlib import Path

_ADMIN_FILE = Path(__file__).resolve().parent.parent / "admins.json"

try:
    with _ADMIN_FILE.open("r", encoding="utf-8") as f:
        _data = json.load(f)
        ADMINS = set(_data.get("admins", []))
except FileNotFoundError:
    ADMINS = set()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS
