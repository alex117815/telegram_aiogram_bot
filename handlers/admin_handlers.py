from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from db_handler.db_handler import PostgresHandler
from create_bot import bot
from helpers.get_admins import get_admins
from keyboards.admin_kb import admin_kb_start
from typing import Optional

start_adm_router = Router()

async def admin_message_start(message: Message):
    user_id = message.from_user.id
    await message.answer('🙋‍♂️ Привет, админ!\n💁‍♂️Чем могу быть полезен?', reply_markup=admin_kb_start)
    pg = PostgresHandler()
    
    admin = pg.get_admin(user_id)
    if not admin:
        pg.update_admin(user_id, True)
