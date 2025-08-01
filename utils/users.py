import json
from pathlib import Path
from typing import Dict

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
