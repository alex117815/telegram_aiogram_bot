from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from db_handler.db_server import PostgresHandlerServer
from aiogram.filters.callback_data import CallbackData
from aiogram.types.chat_member_updated import ChatMemberUpdated

logger = logging.getLogger(__name__)

def user_mute_kb(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🗣️ Размутить', callback_data=f'unmute_user={user_id}')
            ]
        ]
    )

def all_users_kb(server_id, page=1):
    try:
        db = PostgresHandlerServer()
        max_buttons = 10
        inline_keyboard = []
        users_ids = db.get_user_ids(server_id)
        
        # Пагинация
        start_index = (page - 1) * max_buttons
        end_index = start_index + max_buttons
        users_ids_page = users_ids[start_index:end_index]
        
        for user_id in users_ids_page:
            logger.info(f"Processing user ID: {user_id} from {users_ids}")
            user = db.get_user(server_id, user_id[0])
            if user:
                user_name = user.username
                logger.info(f"Found user: {user_name}")
                button = InlineKeyboardButton(text=f'👤 {user_name}', callback_data=f'User_{user_id[0]}')
                inline_keyboard.append([button])
                logger.info(f"Added button for User_{user_id[0]}")
            else:
                logger.info(f"User not found for ID: {user_id[0]}")
        
        # Кнопка "перелистывания страницы"
        if len(users_ids) > end_index:
            next_page_button = InlineKeyboardButton(text='Следующая страница', callback_data=f'NextPage_{page+1}')
            inline_keyboard.append([next_page_button])
        
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, resize_keyboard=True, one_time_keyboard=True)
    except Exception as e:
        logger.error(f"Error in all_users_kb: {e}")

def create_unban_kb(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Разбанить', callback_data=f'unban_user={user_id}')
            ]
        ]
    )

def approve_new_user(server_id, user_id):
    try:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='👉 Я не робот 👈', 
                        callback_data=f"approve_new_user={user_id}_serverid={server_id}"
                    )
                ]
            ]
        )
    except Exception as e:
        logger.error(f"Error in approve_new_user: {e}")

def create_settings_kb(server_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='👋 Приветствовать пользователей', callback_data=f'welcome_users={server_id}'),
                InlineKeyboardButton(text='😢 Прощаться с пользователями', callback_data=f'goodbye_users={server_id}')
            ]
        ]
    )