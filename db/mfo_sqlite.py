import sqlite3
from typing import List, Set
import logging

DB_PATH = "mfo.db"
MAX_SQLITE_PARAMS = 900  

def search_mfo_by_phones(phones: List[str]) -> Set[str]:
    found = set()
    phones = [str(p).strip() for p in phones if str(p).strip().isdigit()]
    if not phones:
        return found

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for i in range(0, len(phones), MAX_SQLITE_PARAMS):
            chunk = phones[i:i + MAX_SQLITE_PARAMS]
            placeholders = ",".join("?" for _ in chunk)
            query = f"SELECT DISTINCT mobile_phone FROM mfo_records WHERE mobile_phone IN ({placeholders})"
            cursor.execute(query, chunk)
            rows = cursor.fetchall()
            found.update(str(row[0]) for row in rows if row[0] is not None)

    except Exception as e:
        logging.exception(f"❌ Ошибка при поиске в MFO: {e}")
    finally:
        conn.close()

    return found
