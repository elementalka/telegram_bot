from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from states.mfo_check_state import MFOCheckState
from datetime import datetime
from pathlib import Path
import pandas as pd
import os
import chardet
from db.mfo_sqlite import search_mfo_by_phones
from keyboards.inline_main import main_inline_kb
import re

router = Router()

@router.callback_query(F.data == "check_mfo")
async def start_mfo_check(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MFOCheckState.waiting_for_phone_file)
    await callback.message.answer(
        "МФО 📂 Пришли .txt, .csv или .xlsx, .xls) файл с телефонами в первой колонке.\n"
        "На выходе — файл с отметкой: найден ли номер в базе МФО."
    )

@router.message(MFOCheckState.waiting_for_phone_file, F.document)
async def handle_mfo_file(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    document = message.document

    if not document.file_name.endswith((".txt", ".csv", ".xlsx", ".xls")):
        await message.answer("❌ Поддерживаются только .txt, .csv и Excel (.xlsx, .xls) файлы.")
        return

    path = f"data/user_data/{user_id}"
    os.makedirs(path, exist_ok=True)
    input_path = Path(path) / f"mfo_{document.file_id}{Path(document.file_name).suffix}"
    await message.bot.download(document, destination=input_path)

    with open(input_path, "rb") as f:
        raw = f.read(2048)
        encoding = chardet.detect(raw)["encoding"] or "utf-8"

    try:
        if input_path.suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(input_path, usecols=[0], header=None, dtype=str)
        else:
            df = pd.read_csv(input_path, usecols=[0], header=None, dtype=str, encoding=encoding, engine="python")
    except Exception as e:
        await message.answer(f"❌ Ошибка при чтении файла: {e}")
        return

    def clean_phone(val):
        try:
            val = str(val).replace(",", ".").strip()
            if 'e' in val.lower():
                val = str(int(float(val)))
            val = ''.join(filter(str.isdigit, val))
            if val.startswith("87"):
                val = "77" + val[2:]
            return val if len(val) == 11 and val.startswith("77") else None
        except:
            return None

    phones = [clean_phone(val) for val in df.iloc[:, 0]]
    phones = [p for p in phones if p]  # удаляем None

    if not phones:
        await message.answer("❌ Не найдено ни одного корректного номера телефона.")
        return

    found = search_mfo_by_phones(phones)

    output_path = Path(path) / f"result_mfo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    df_out = pd.DataFrame({"Телефон": phones})
    df_out["В МФО"] = df_out["Телефон"].apply(lambda x: "Да" if x in found else "Нет")

    df_yes = df_out[df_out["В МФО"] == "Да"]
    df_no = df_out[df_out["В МФО"] == "Нет"]

    path_yes = Path(path) / f"mfo_найдены_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path_no = Path(path) / f"mfo_чистые_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    df_yes.to_excel(path_yes, index=False)
    df_no.to_excel(path_no, index=False)

    await message.answer_document(FSInputFile(path_yes), caption="✅ Найденные в базе МФО")
    await message.answer_document(FSInputFile(path_no), caption="✅ Не найдены в базе МФО")

    await message.answer("📍 Что дальше?", reply_markup=main_inline_kb)


