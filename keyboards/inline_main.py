from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Проверить базу", callback_data="check_menu")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Другие фильтры", callback_data="other_filters")]
    ]
)

# Меню выбора проверки базы
check_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="МФО", callback_data="check_mfo")],
        [InlineKeyboardButton(text="Прозвон", callback_data="check_call")],
        [InlineKeyboardButton(text="Прозвон и МФО", callback_data="check_call_mfo")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ]
)

# Меню других фильтров
other_filters_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Активность номера", callback_data="filter_activity")],
        [InlineKeyboardButton(text="WhatsApp", callback_data="check_ws")],
        [InlineKeyboardButton(text="Должники Казахстан", callback_data="filter_debt_kz")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ]
)
