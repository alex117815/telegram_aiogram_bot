from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging

logger = logging.getLogger(__name__)

admin_kb_start = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🔄 Всего пользователей', callback_data='all_users')],
        [InlineKeyboardButton(text='💎 Инфо о юзере', callback_data='user_info'), InlineKeyboardButton(text="🔒 Статистика", callback_data="Statistico")],
        [InlineKeyboardButton(text='👑 Админ-профиль', callback_data='adm_profile'), InlineKeyboardButton(text='👤 Профиль', callback_data='profile')],
        [InlineKeyboardButton(text='👨‍👨‍👧‍👧 Рассылка', callback_data='send_mess'), InlineKeyboardButton(text="📝Тикеты", callback_data='tickets')],
        [InlineKeyboardButton(text='📲 Добавить админа', callback_data='add_admin'), InlineKeyboardButton(text='💉 Удалить админа', callback_data='del_admin')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

admin_kb_cancel = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

admin_kb_skip_or_cancel = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='⏭ Пропустить', callback_data='skip_image_spam'),
            InlineKeyboardButton(text='❌ Отмена', callback_data='cancel')
        ],
    ],
    resize_keyboard=True
)

def create_tickets_kb(tickets):
    try:
        max_buttons = 10
        inline_keyboard = []
        for ticket in tickets[:max_buttons]:
            button = InlineKeyboardButton(text=f'🗣️ {ticket.ticket_id}', callback_data=f'Ticket{ticket.ticket_id}')
            inline_keyboard.append([button])
            logger.info(f"Ticket{ticket.ticket_id}")
        
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, resize_keyboard=True, one_time_keyboard=True)

    except Exception as e:
        logger.error(e)

def create_ticket_actions_kb(ticket_id):
    try:
        ticket_actions = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='✅ Принять', callback_data=f'accept_ticket={ticket_id}'),
                    InlineKeyboardButton(text='❌ Отклонить', callback_data=f'reject_ticket={ticket_id}'),
                ],
                [
                    InlineKeyboardButton(text='🔙 Вернуться', callback_data=f'back_to_ticket_list'),
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        return ticket_actions
    except Exception as e:
        logger.error(e)

def open_ticket_actions_kb(ticket_id):
    try:
        ticket_actions = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='✅ Написать', callback_data=f'message_ticket={ticket_id}'),
                    InlineKeyboardButton(text='❌ Закрыть', callback_data=f'reject_ticket={ticket_id}'),
                ],
                [
                    InlineKeyboardButton(text='🔙 Вернуться', callback_data=f'back_to_ticket_list'),
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        return ticket_actions
    except Exception as e:
        logger.error(e)

def stop_tickets_kb(ticket_id):
    try:
        ticket_actions = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='❌ Остановить диалог'),
                ]
            ],
            resize_keyboard=True,
            input_field_placeholder="Введите текст или же нажмите на кнопку ниже",
        )
        return ticket_actions
    except Exception as e:
        logger.error(e)

def continute_tickets_kb(ticket_id):
    try:
        ticket_actions = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='✅ Продолжить диалог'),
                ]
            ],
            resize_keyboard=True,
            input_field_placeholder="Введите текст или же нажмите на кнопку ниже",
        )
        return ticket_actions
    except Exception as e:
        logger.error(e)

def profile_actions_kb(user_id):
    try:
        ticket_actions = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='🚫 Забанить', callback_data=f'ban_profile={user_id}'),
                    InlineKeyboardButton(text='💬 Написать', callback_data=f'message_profile={user_id}'),
                ],
                [
                    InlineKeyboardButton(text='🔙 Вернуться', callback_data=f'cancel'),
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        return ticket_actions
    except Exception as e:
        logger.error(e)

def unban_profile_kb(user_id):
    try:
        ticket_actions = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='✅ Разбанить', callback_data=f'unban_profile={user_id}'),
                ],
                [
                    InlineKeyboardButton(text='🔙 Вернуться', callback_data=f'cancel'),
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        return ticket_actions
    except Exception as e:
        logger.error(e)

create_spam_type_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='В бота', callback_data='spam_in_bot'),
            InlineKeyboardButton(text='На сервера', callback_data='spam_in_server'),
        ],
        [
            InlineKeyboardButton(text='🔙 Вернуться', callback_data='cancel'),
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)