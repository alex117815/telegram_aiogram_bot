from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from matplotlib.backend_bases import key_press_handler

user_kb_start = InlineKeyboardMarkup( #пример inline-keyboard для юзера
    inline_keyboard=[
        [
            InlineKeyboardButton(text='👤 Профиль', callback_data='profile'),
            InlineKeyboardButton(text='📝 Написать тикет', callback_data='write_ticket'),
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

skip_or_cancel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='⏭ Пропустить'),
            KeyboardButton(text='❌ Отмена')
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите способ"
)

verified_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='✅ Верифицировать', request_contact=True),
        ]
    ],
    resize_keyboard=True
)

add_to_server = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='➕ Добавить', url="https://t.me/KeaxyFunBot?startgroup=start")
        ]
    ]
)

cancel_kb_user = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='❌ Назад', callback_data='cancel_user_kb')
        ]
    ]
)