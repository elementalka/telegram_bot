import json
from pathlib import Path
from typing import Dict
from datetime import datetime

USER_FILE = Path(__file__).resolve().parent.parent / "users.json"


def _load_data() -> Dict[str, Dict]:
    if USER_FILE.exists():
        try:
            with USER_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_data(data: Dict[str, Dict]):
    USER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USER_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_balance(user_id: int) -> float:
    data = _load_data()
    return float(data.get(str(user_id), {}).get("balance", 0))


def deduct_balance(user_id: int, amount: float) -> bool:
    data = _load_data()
    user = data.setdefault(str(user_id), {"balance": 0})
    if user["balance"] < amount:
        return False
    user["balance"] -= amount
    _save_data(data)
    return True


def add_balance(user_id: int, amount: float):
    data = _load_data()
    user = data.setdefault(str(user_id), {"balance": 0})
    user["balance"] += amount
    _save_data(data)


def register_user(user_id: int, name: str, username: str) -> bool:
    """Add a user to users.json if not present.

    Returns True if a new record was created.
    """
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": 0,
            "name": name,
            "username": username,
            "created_at": datetime.utcnow().isoformat()
        }
        _save_data(data)
        return True
    return False


def get_user(user_id: int) -> Dict:
    data = _load_data()
    return data.get(str(user_id), {})
