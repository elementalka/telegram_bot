from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from utils.admins import is_admin
from aiogram.fsm.context import FSMContext
from states.arrest_check_state import ArrestCheckState
from states.mfo_check_state import MFOCheckState
from keyboards.inline_main import main_inline_kb
router = Router()

main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚨 Чекер арестов КЗ", callback_data="check_arrest")],
    [InlineKeyboardButton(text="💸 Чек МФО", callback_data="check_mfo")]
])

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    kb = list(main_inline_kb.inline_keyboard)
    if is_admin(message.from_user.id):
        kb.append([InlineKeyboardButton(text="🛠 Админ", callback_data="admin_panel")])
    await message.answer("Выберите действие:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

