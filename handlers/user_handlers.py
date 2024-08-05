from aiogram import Router
from aiogram.types import Message
from keyboards.user_kb import user_kb_start

start_usr_router = Router()

async def user_message_start(message: Message):
    await message.answer('🙋‍♂️ Привет, юзер, чем могу помочь?', reply_markup=user_kb_start)