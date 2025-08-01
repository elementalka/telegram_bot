# checkers/kz_checker.py
import requests
import pandas as pd
import logging
import random
import time
import os
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime
import chardet
from collections import defaultdict
from pathlib import Path
captcha_token = ''
USE_PROXIES = True
MAX_THREADS = 10

MAX_GLOBAL_RPS = 1.0
PAUSE_EVERY = 1000
PAUSE_DURATION = 20
ERROR_PAUSE_TIME = 180
FAILURE_THRESHOLD = 0.2
FAILURE_PAUSE_TIME = 60 
TIMEOUT_THRESHOLD = 5
TIMEOUT_SLEEP = 10

adaptive_delay = {"delay": 2.0}
proxies_list = []
proxy_index = 0
proxy_stats = defaultdict(lambda: {"timeouts": 0, "used": 0})
last_request_time = 0

ALL_COLUMNS = [
    "ИНН",
    'Арест на банковские счета',
    'Запрет на выезд',
    'Запрет на регистрационные действия',
    'Е-Нотариат',
    'Арест на имущество',
    'Арест на транспорт',
    'Общий арест',
    'Ошибка'
]

def load_proxies():
    global proxies_list
    if not proxies_list:
        with open("proxies.txt", "r", encoding="utf-8") as f:
            raw = [line.strip() for line in f if line.strip()]
            for line in raw:
                parts = line.split(":")
                if len(parts) == 4:
                    ip, port, login, password = parts
                    proxy = f"http://{login}:{password}@{ip}:{port}"
                elif len(parts) == 2:
                    ip, port = parts
                    proxy = f"http://{ip}:{port}"
                else:
                    continue
                proxies_list.append(proxy)
        random.shuffle(proxies_list)
        print(f"✅ Загружено прокси: {len(proxies_list)}")

def get_next_proxy():
    global proxy_index
    attempts = 0
    while attempts < len(proxies_list):
        proxy = proxies_list[proxy_index % len(proxies_list)]
        proxy_index += 1
        if proxy_stats[proxy]["timeouts"] < 5:
            proxy_stats[proxy]["used"] += 1
            return {"http": proxy, "https": proxy}
        attempts += 1
    return None

def throttle():
    global last_request_time
    now = time.time()
    elapsed = now - last_request_time
    min_interval = 1.0 / MAX_GLOBAL_RPS
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    last_request_time = time.time()

def get_site_data(inn: str, proxy: dict, max_retries=3):
    url = "https://aisoip.adilet.gov.kz/rest/debtor/findArrest"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': 'https://aisoip.adilet.gov.kz',
        'Referer': 'https://aisoip.adilet.gov.kz/forCitizens/findArest'
    }
    payload = {"action": "findArrest", "bin": "", "captcha": captcha_token, "iin": inn}

    for attempt in range(max_retries):
        try:
            throttle()
            response = requests.post(url, headers=headers, json=payload, timeout=10, proxies=proxy)
        
            if response.status_code == 200:
                adaptive_delay["delay"] = max(1.0, adaptive_delay["delay"] * 0.95)
                return response.json(), None
            elif response.status_code == 400:
                logging.warning(f"[{inn}] ❗ Некорректный ИИН (400)")
                return None, "invalid_iin"
            elif response.status_code in (429, 403):
                logging.warning(f"[{inn}] Код {response.status_code} — уходим на паузу {ERROR_PAUSE_TIME} сек")
                time.sleep(ERROR_PAUSE_TIME)        

        except Exception as e:
            logging.warning(f"[{inn}] Ошибка: {e}")
            adaptive_delay["delay"] = min(30.0, adaptive_delay["delay"] * 1.5)
        time.sleep(adaptive_delay["delay"])
    return None, "timeout"

def normalize_inn(val):
    try:
        original = str(val).strip().lower()

        if 'e' in original or not original.replace('.', '').replace(',', '').replace(' ', '').isdigit():
            return None

        digits_only = ''.join(filter(str.isdigit, original))

        if len(digits_only) != 12:
            return None

        if digits_only.endswith("0000"):  # <= новая фильтрация
            return None

        return digits_only
    except:
        return None

def process_inn_with_proxy(row, timeout_counter):
    inn = normalize_inn(row.iloc[0])
    proxy = get_next_proxy() if USE_PROXIES else None
    site_data, error = get_site_data(inn, proxy)

    if site_data:
        arrest_data = {key: '' for key in ALL_COLUMNS[1:-2]}  # поля без ИНН и Общий арест, Ошибка
        for item in site_data:
            name = item['name_ru']
            if name in arrest_data:
                arrest_data[name] = 'Да' if item.get('arrestFound', False) else 'Нет'
        arrest_data["Общий арест"] = "Да" if any(val == 'Да' for val in arrest_data.values()) else "Нет"
        arrest_data["Ошибка"] = ""
        return {**row.to_dict(), **arrest_data}, False

    else:
        # Не считаем критической ошибкой плохие ИИНы
        if error in ("timeout", "Ошибка получения данных"):
            timeout_counter.append(1)
            critical = True
        elif error == "invalid_iin":
            critical = False
        return {
            **row.to_dict(),
            'Общий арест': '',
            'Ошибка': error or 'Ошибка получения данных'
        }, critical
def check_arrest_file(user_id: int, input_path: str, output_path: str, progress_tracker=None, chunk_offset: int = 0):
    if progress_tracker is None:
        from checkers.arrest_queue import progress_tracker as default_tracker
        progress_tracker = default_tracker

    with open(input_path, "rb") as f:
        raw_data = f.read(2048)
        encoding = chardet.detect(raw_data)["encoding"] or "utf-8"

    if input_path.lower().endswith(".xlsx"):
        df = pd.read_excel(input_path, usecols=[0], header=None, dtype=object, engine="openpyxl")
    elif input_path.lower().endswith(".xls"):
        df = pd.read_excel(input_path, usecols=[0], header=None, dtype=object, engine="xlrd")
    else:
        df = pd.read_csv(input_path, usecols=[0], header=None, dtype=object, encoding=encoding)

    df.columns = ["ИНН"]
    df["ИНН"] = df["ИНН"].map(normalize_inn)
    df = df[df["ИНН"].str.len() == 12]  # фильтрация по длине

    if USE_PROXIES:
        load_proxies()

    if os.path.exists(output_path):
        os.remove(output_path)

    pd.DataFrame(columns=ALL_COLUMNS).to_csv(output_path, index=False, encoding="utf-8-sig")

    start_index = 0

    if user_id not in progress_tracker:
        progress_tracker[user_id] = {
            "total": chunk_offset + len(df),
            "done": chunk_offset
        }

    while start_index < len(df):
        batch = df.iloc[start_index:start_index + 100]
        new_data, timeout_counter = [], []

        with ThreadPoolExecutor(max_workers=min(MAX_THREADS, len(batch))) as executor:
            futures = [executor.submit(process_inn_with_proxy, row, timeout_counter) for _, row in batch.iterrows()]
            results = [f.result() for f in futures]

        new_data = [r[0] for r in results]
        error_count = sum(1 for r in results if r[1])

        with open(output_path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=ALL_COLUMNS)
            for row in new_data:
                writer.writerow({key: row.get(key, "") for key in ALL_COLUMNS})

        start_index += len(batch)
        progress_tracker[user_id]["done"] = chunk_offset + start_index

        if error_count / len(batch) >= FAILURE_THRESHOLD:
            logging.warning(f"❗ Высокий процент ошибок ({error_count}/{len(batch)}). Пауза {FAILURE_PAUSE_TIME} сек")
            time.sleep(FAILURE_PAUSE_TIME)

        if start_index % PAUSE_EVERY == 0:
            logging.info(f"⏸️ Пауза {PAUSE_DURATION} сек после {start_index} строк")
            time.sleep(PAUSE_DURATION)

        time.sleep(random.uniform(1.0, 3.0))

    df_final = pd.read_csv(output_path, encoding="utf-8-sig")

    positive = df_final[df_final["Общий арест"] == "Да"]
    clean = df_final[df_final["Общий арест"] == "Нет"]

    base_path = Path(output_path)
    positive_path = base_path.with_name(base_path.stem + "_аресты.xlsx")
    clean_path = base_path.with_name(base_path.stem + "_без_арестов.xlsx")

    positive.to_excel(positive_path, index=False)
    clean.to_excel(clean_path, index=False)

    try:
        os.remove(output_path)
    except Exception as e:
        logging.warning(f"⚠️ Не удалось удалить временный CSV: {e}")

    logging.info(f"📂 Сохранены: {positive_path.name} (аресты), {clean_path.name} (чистые)")

    progress_tracker.pop(user_id, None)
    logging.info(f"[User {user_id}] Обработка завершена: {output_path}")

    return True, str(positive_path), str(clean_path)
