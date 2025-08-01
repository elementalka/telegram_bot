from aiogram import Router, types, F
from utils.admins import is_admin
from whatsapp.session import create_session, delete_session

router = Router()

admin_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="🔑 Подключить WhatsApp", callback_data="add_ws")],
    [types.InlineKeyboardButton(text="❌ Удалить сессию", callback_data="del_ws")]
])

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await callback.message.answer("🛠 Админ панель:", reply_markup=admin_kb)

@router.callback_query(F.data == "add_ws")
async def add_ws(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await callback.message.answer("⏳ Создаю сессию…")
    await create_session(callback.bot, callback.from_user.id)

@router.callback_query(F.data == "del_ws")
async def del_ws(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await delete_session()
    await callback.message.answer("✅ Сессия удалена")
