from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiohttp import ClientSession
from states.ws_check_state import WSCheckState
from keyboards.inline_main import main_menu_kb
import os

WS_CHECKER_URL = os.getenv("WS_CHECKER_URL", "http://localhost:3000")

router = Router()

choice_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Проверить вручную")],
        [KeyboardButton(text="Загрузить файл (.txt/.csv)")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

@router.callback_query(F.data == "check_ws")
async def start_ws(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WSCheckState.choosing)
    await callback.message.answer(
        "Привет! Выберите способ проверки номеров:",
        reply_markup=choice_kb,
    )

@router.message(WSCheckState.choosing, F.text == "Проверить вручную")
async def choose_manual(message: types.Message, state: FSMContext):
    await state.set_state(WSCheckState.manual)
    await message.answer(
        "Пришлите один или несколько номеров (каждый с новой строки).\n"
        "Формат: +71234567890 или 71234567890",
        reply_markup=ReplyKeyboardRemove(),
    )

@router.message(WSCheckState.choosing, F.text.startswith("Загрузить файл"))
async def choose_file(message: types.Message, state: FSMContext):
    await state.set_state(WSCheckState.file)
    await message.answer(
        "Загрузите файл .txt или .csv со списком номеров (по одному в строке).",
        reply_markup=ReplyKeyboardRemove(),
    )

@router.message(WSCheckState.manual, F.text)
async def process_manual(message: types.Message, state: FSMContext):
    lines = [l.strip() for l in message.text.splitlines() if l.strip()]
    numbers = [l if l.startswith("+") else "+" + l for l in lines]
    await message.answer(f"Проверяю {len(numbers)} номеров…")

    async with ClientSession() as sess:
        async with sess.post(f"{WS_CHECKER_URL}/check", json={"numbers": numbers}) as resp:
            if resp.status != 200:
                await message.answer(
                    f"Ошибка сервиса: {resp.status} {await resp.text()}"
                )
                await state.clear()
                return
            results = await resp.json()

    out = []
    for n in numbers:
        mark = "✅" if results.get(n) else "❌"
        out.append(f"{n}: {mark}")

    await message.answer("\n".join(out), reply_markup=main_menu_kb)
    await state.clear()

@router.message(WSCheckState.file, F.document)
async def process_file(message: types.Message, state: FSMContext):
    doc = message.document
    fname = doc.file_name.lower()
    if not (fname.endswith(".txt") or fname.endswith(".csv")):
        await message.answer("Нужен файл .txt или .csv")
        return

    bio = await (await doc.get_file()).download_as_bytearray()
    text = bio.decode("utf-8", errors="ignore").splitlines()
    numbers = [l.strip() for l in text if l.strip()]
    numbers = [l if l.startswith("+") else "+" + l for l in numbers]
    await message.answer(f"Проверяю {len(numbers)} номеров из файла…")

    async with ClientSession() as sess:
        async with sess.post(f"{WS_CHECKER_URL}/check", json={"numbers": numbers}) as resp:
            if resp.status != 200:
                await message.answer(
                    f"Ошибка сервиса: {resp.status} {await resp.text()}"
                )
                await state.clear()
                return
            results = await resp.json()

    ok = [n for n, v in results.items() if v]
    out_txt = "\n".join(ok) or "— Пусто —"

    await message.answer_document(
        document=out_txt.encode("utf-8"),
        filename="whatsapp_valid.txt",
    )
    await message.answer("📍 Что дальше?", reply_markup=main_menu_kb)
    await state.clear()

@router.message(WSCheckState.manual)
@router.message(WSCheckState.file)
async def wrong_input(message: types.Message):
    await message.answer("❌ Неверный формат. Попробуйте ещё раз или нажмите /cancel")

@router.message(F.text == "/cancel")
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
