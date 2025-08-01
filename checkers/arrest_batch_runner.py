import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from checkers.kz_checker import check_arrest_file
import shutil
import chardet

CHUNK_SIZE = 10000

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

def is_clean_input(val):
    if isinstance(val, float):
        return False
    val_str = str(val).strip().lower()
    if "e" in val_str or "." in val_str:
        return False
    return True
def run_arrest_check_in_chunks(user_id, input_path, final_output_path, progress_tracker=None):
    input_path = Path(input_path)
    if progress_tracker is None:
        from checkers.arrest_queue import progress_tracker as default_tracker
        progress_tracker = default_tracker

    temp_dir = Path(final_output_path).parent / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(temp_dir, exist_ok=True)

    with open(input_path, "rb") as f:
        raw = f.read(2048)
        encoding = chardet.detect(raw)["encoding"] or "utf-8"

    if input_path.suffix in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(input_path, usecols=[0], header=None, dtype=str, engine="openpyxl")
        except Exception as e:
            # Файл с расширением Excel, но не является настоящим Excel — читаем как CSV
            df = pd.read_csv(input_path, usecols=[0], header=None, encoding="utf-8", engine="python")
    else:
        df = pd.read_csv(input_path, usecols=[0], header=None, encoding="utf-8", engine="python")


    df.columns = ["ИНН"]

    before_count = len(df)

    df = df[df["ИНН"].map(is_clean_input)]

    df["ИНН"] = df["ИНН"].map(normalize_inn)
    df = df.dropna(subset=["ИНН"])

    after_count = len(df)

    skipped_count = before_count - after_count
    if skipped_count > 0:
        print(f"⚠️ Пропущено {skipped_count} некорректных ИНН (e+ или не 12 цифр)")

    progress_tracker[user_id] = {"total": len(df), "done": 0}

    positives, cleans = [], []

    for i, chunk_start in enumerate(range(0, len(df), CHUNK_SIZE)):
        chunk_df = df.iloc[chunk_start:chunk_start + CHUNK_SIZE]
        chunk_file = temp_dir / f"chunk_{i}.csv"
        chunk_df.to_csv(chunk_file, index=False, header=False, encoding="utf-8-sig")

        output_chunk = temp_dir / f"result_{i}.csv"
        result, positive_path, clean_path = check_arrest_file(
            user_id=user_id,
            input_path=str(chunk_file),
            output_path=str(output_chunk),
            progress_tracker=progress_tracker,
            chunk_offset=chunk_start
        )
        if not result:
            raise Exception(f"❌ Ошибка при обработке чанка {i}")

        if not os.path.exists(positive_path):
            raise FileNotFoundError(f"❌ Файл с арестами не найден: {positive_path}")
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"❌ Файл без арестов не найден: {clean_path}")
        
        positives.append(positive_path)
        cleans.append(clean_path)
        print(f"🧩 Чанк {i + 1} из {((len(df) - 1) // CHUNK_SIZE) + 1} обработан")

    final_positive_path = Path(final_output_path).with_name(Path(final_output_path).stem + "_аресты.xlsx")
    final_clean_path = Path(final_output_path).with_name(Path(final_output_path).stem + "_без_арестов.xlsx")

    pd.concat([pd.read_excel(f) for f in positives], ignore_index=True).to_excel(final_positive_path, index=False)
    pd.concat([pd.read_excel(f) for f in cleans], ignore_index=True).to_excel(final_clean_path, index=False)

    return True, str(final_positive_path), str(final_clean_path), skipped_count
