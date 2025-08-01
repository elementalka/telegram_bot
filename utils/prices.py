import json
from pathlib import Path

PRICE_FILE = Path(__file__).resolve().parent.parent / "prices.json"


def get_price(key: str) -> float:
    if PRICE_FILE.exists():
        try:
            with PRICE_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return float(data.get(key, 0))
        except Exception:
            return 0
    return 0
