from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_inline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚨 Чекер арестов КЗ", callback_data="check_arrest")],
    [InlineKeyboardButton(text="💸 Чек МФО", callback_data="check_mfo")],
    [InlineKeyboardButton(text="📱 Чек WhatsApp", callback_data="check_ws")]
])
