from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.admins import is_admin
from utils.users import register_user, get_user, get_balance
from keyboards.inline_main import main_menu_kb, check_menu_kb, other_filters_kb

router = Router()

WELCOME_TEXT = (
    "Добро пожаловать в КЦ БАЗА МАСТЕР.\n"
    "Наш бот собирает в себе прозвоненную базу более чем С 300 офисов ежедневно, не учитывая новые команды которые постоянно присоединяются. Также бот содержит в себе базу номеров, которые являются клиентами МФО.\n\n"
    "ЧТО БУДЕТ С ВАШЕЙ БАЗОЙ, ПОСЛЕ ТОГО КАК ОНА ПОПАДЕТ В БОТ?\n"
    "Для обработки бот использует только данные номеров телефонов. Номера будут добавлены в список прозвоненных через некоторое время. База данных может использоваться только в целях улучшения бота.\n"
    "Таким образом мы не храним кучу лишнего веса на серверах и ваша база не может попасть в чьи-то руки."
)

MENU_TEXT = (
    "ГЛАВНОЕ МЕНЮ\n"
    "Для дальнейших действий используйте кнопки меню, либо команды.\n\n"
    "КОМАНДЫ:\n"
    "/start - главное меню;\n"
    "/check - проверить базу;\n"
    "/profile - профиль;\n"
    "/stats - статистика;\n"
    "/help - помощь/информация."
)


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    is_new = register_user(message.from_user.id, message.from_user.first_name or "-", message.from_user.username or "-")
    if is_new:
        await message.answer(WELCOME_TEXT)
    await send_main_menu(message)


async def send_main_menu(message: Message):
    kb = list(main_menu_kb.inline_keyboard)
    if is_admin(message.from_user.id):
        kb.append([InlineKeyboardButton(text="🛠 Админ", callback_data="admin_panel")])
    await message.answer(MENU_TEXT, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@router.message(F.text == "/check")
async def cmd_check(message: Message):
    await message.answer(
        "Наш сервис может выполнять объем файлов до 20мб за раз!\n\n"
        "\ud83d\udcc3 После выбора проверки, просто отправьте вашу базу в виде Excel файла.\n"
        "\ud83d\udd0e Бот выполнит проверку и отправит вам результаты в том же формате, без потери данных.\n"
        "-> Инструкция по проверке (https://telegra.ph/PROVERIT-BAZU-glavnoe-menyu-11-10)",
        reply_markup=check_menu_kb,
    )


@router.message(F.text == "/profile")
async def cmd_profile(message: Message):
    user = get_user(message.from_user.id)
    balance = get_balance(message.from_user.id)
    created = user.get("created_at", "-")
    await message.answer(
        f"#\ufe0f\u20e3 ID: {message.from_user.id}\n"
        f"\ud83d\udc64 Имя: {message.from_user.first_name}\n"
        f"\ud83d\udd17 Никнейм: @{message.from_user.username if message.from_user.username else '—'}\n\n"
        f"\u2b55\ufe0f Баланс: {balance:.2f} $\n"
        f"\ud83d\udccb Дата регистрации: {created}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Пополнить баланс", callback_data="topup")],[InlineKeyboardButton(text="Назад", callback_data="main_menu")]])
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    await message.answer(
        "Наш бот собирает в себе прозвоненную базу более чем С 300 офисов ежедневно, не учитывая новые команды которые постоянно присоединяются. Также бот содержит в себе базу номеров, которые являются клиентами МФО.\n\n"
        "ЧТО БУДЕТ С ВАШЕЙ БАЗОЙ, ПОСЛЕ ТОГО КАК ОНА ПОПАДЕТ В БОТ?\n"
        "Для обработки бот использует только данные номеров телефонов. Номера будут добавлены в список прозвоненных через некоторое время. База данных может использоваться только в целях улучшения бота.\n"
        "Таким образом мы не храним кучу лишнего веса на серверах и ваша база не может попасть в чьи-то руки.\n\n"
        "Канал с информацией (https://t.me/Master_bazy)\n"
        "Знакомство с ботом (https://t.me/Master_bazy/22)\n"
        "Подробный FAQ (https://t.me/Master_bazy/21)\n"
        "Задать вопрос Админу (https://t.me/baza_master)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="main_menu")]])
    )


@router.message(F.text == "/stats")
async def cmd_stats(message: Message):
    await message.answer(
        "Статистика недоступна в данной версии бота.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="main_menu")]])
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_cb(callback: CallbackQuery):
    await send_main_menu(callback.message)
    await callback.answer()


@router.callback_query(F.data == "check_menu")
async def check_menu_cb(callback: CallbackQuery):
    await cmd_check(callback.message)
    await callback.answer()


@router.callback_query(F.data == "other_filters")
async def other_filters_cb(callback: CallbackQuery):
    await callback.message.answer("Выберите фильтр:", reply_markup=other_filters_kb)
    await callback.answer()


@router.callback_query(F.data == "filter_activity")
async def activity_stub(callback: CallbackQuery):
    await callback.message.answer(
        "\ud83d\udd0e ПРОВЕРКА АКТИВНОСТИ НОМЕРА\n(ЛЮБАЯ СТРАНА)\n\n"
        "Услуга выполняется через администратора. Напишите @baza_master" ,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="other_filters")]])
    )
    await callback.answer()


@router.callback_query(F.data == "filter_debt_kz")
async def debt_stub(callback: CallbackQuery):
    await callback.message.answer(
        "\ud83d\udd0e ПРОВЕРКА ДОЛЖНИКОВ (КАЗАХСТАН)\n\n"
        "Услуга выполняется через администратора. Напишите @baza_master" ,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="other_filters")]])
    )
    await callback.answer()


@router.callback_query(F.data.in_("check_call", "check_call_mfo"))
async def call_stub(callback: CallbackQuery):
    await callback.message.answer("Функция в разработке", reply_markup=check_menu_kb)
    await callback.answer()
