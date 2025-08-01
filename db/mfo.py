# db/mfo.py
import sqlite3

def search_phones_in_mfo_db(phones: list[str]) -> set[str]:
    conn = sqlite3.connect("mfo.db")
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(phones))
    query = f"SELECT DISTINCT phone FROM mfo WHERE phone IN ({placeholders})"

    cursor.execute(query, phones)
    found = {row[0] for row in cursor.fetchall()}

    conn.close()
    return found
