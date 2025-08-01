from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from states.arrest_check_state import ArrestCheckState
from checkers.arrest_queue import enqueue_check, progress_tracker
from datetime import datetime
from pathlib import Path
import pandas as pd
import os
import chardet
from checkers.arrest_batch_runner import normalize_inn

router = Router()
@router.callback_query(F.data == "check_arrest")
async def start_arrest_check(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ArrestCheckState.waiting_for_inn_file)
    await callback.message.answer(
        "АРЕСТЫ 📂 Пришлите .csv или .txt или .xlsx файл с ИНН  в первой колонке."
    )
@router.message(ArrestCheckState.waiting_for_inn_file, F.document)
async def process_inn_file(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    document = message.document

    if not document.file_name.endswith((".txt", ".csv", ".xlsx", ".xls")):
        await message.answer("❌ Поддерживаются только .txt, .csv и Excel (.xlsx, .xls) файлы.")
        return

    path = f"data/user_data/{user_id}"
    os.makedirs(path, exist_ok=True)
    input_path = Path(path) / f"arrest_{document.file_id}{Path(document.file_name).suffix}"
    await message.bot.download(document, destination=input_path)

    with open(input_path, "rb") as f:
        raw = f.read(2048)
        encoding = chardet.detect(raw)["encoding"] or "utf-8"

    try:
        

        if input_path.suffix in [".xlsx", ".xls"]:
            try:
                df = pd.read_excel(input_path, usecols=[0], header=None, dtype=object, engine="openpyxl")
            except Exception as e:
                # Попытка fallback на csv
                df = pd.read_csv(input_path, usecols=[0], header=None, encoding="utf-8", engine="python")
        else:
            df = pd.read_csv(input_path, usecols=[0], header=None, encoding="utf-8", engine="python")


    except Exception as e:
        await message.answer(f"❌ Ошибка при чтении файла: {e}")
        return


    df.columns = ["ИНН"]
    before_count = len(df)

    df["ИНН"] = df["ИНН"].map(normalize_inn)
    df = df[df["ИНН"].notnull() & (df["ИНН"].str.len() == 12)]

    after_count = len(df)

    skipped_count = before_count - after_count

    if df.empty:
        await message.answer("❌ Не найдено ни одного корректного ИНН.")
        return

    result_path = Path(path) / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    bot = message.bot


    async def send_ready_file(user_id: int, output_path_arrest: str, output_path_clean: str, error: str = None, skipped_count: int = 0):
        if error:
            await bot.send_message(user_id, f"❌ Произошла ошибка при обработке файла:\n<code>{error}</code>")
            return
        if not os.path.exists(output_path_arrest):
            await bot.send_message(user_id, "❌ Не удалось найти файл с арестами.")
            return
        if not os.path.exists(output_path_clean):
            await bot.send_message(user_id, "❌ Не удалось найти файл без арестов.")
            return
        if skipped_count > 0:
            await bot.send_message(user_id, f"⚠️ Пропущено {skipped_count} некорректных ИНН (напр. в формате '8.01E+11' или не 12 цифр).")

        await bot.send_document(
            user_id,
            document=FSInputFile(output_path_arrest),
            caption="🚨 Найденные аресты:"
        )
        await bot.send_document(
            user_id,
            document=FSInputFile(output_path_clean),
            caption="✅ Чистые ИНН (без арестов):"
        )

        from keyboards.inline_main import main_inline_kb
        await bot.send_message(user_id, "📍 Что дальше?", reply_markup=main_inline_kb)
    df.to_csv(input_path, index=False, header=False, encoding="utf-8-sig")
    success, status = await enqueue_check(user_id, str(input_path), str(result_path), send_ready_file)

    if not success and status == "processing":
        await message.answer("⚠️ У тебя уже идёт проверка. Подожди окончания.")
        from keyboards.inline_main import main_inline_kb
        await bot.send_message(user_id, "📌 Выбери действие:", reply_markup=main_inline_kb)
        return

    note = "\n⏳ Файл поставлен в очередь." if status == "queued" else ""
    await message.answer(f"✅ Файл принят. Начинаем проверку.{note}")

    progress_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Прогресс", callback_data="progress")]
    ])
    await message.answer("📊 Нажми, чтобы узнать прогресс обработки:", reply_markup=progress_kb)

@router.callback_query(F.data == "progress")
async def show_progress_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    prog = progress_tracker.get(user_id)
    if not prog or prog["total"] == 0:
        await callback.message.answer("⏳ Пока ничего не обрабатывается. Пришли файл.")
    else:
        await callback.message.answer(f"🔄 Обработано: {prog['done']} из {prog['total']}.")
