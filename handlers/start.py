from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from db_handler.db_handler import PostgresHandler
from handlers.admin_handlers import admin_message_start
from handlers.user_handlers import user_message_start
from helpers.get_admins import get_admins
from aiogram.enums import ChatType
from aiogram.utils.deep_linking import decode_payload
from create_bot import bot
import logging
from aiogram.types.input_file import FSInputFile
from keyboards.user_kb import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

main_router = Router()

@main_router.message(CommandStart(deep_link=None))
async def cmd_start_ref(message: Message, command: CommandObject):
    try:
        chat_typ = message.chat.type
        if chat_typ != ChatType.PRIVATE:
            return

        db = PostgresHandler()
        user = db.get_user(message.from_user.id)
        admins_id = await get_admins()
        admin = message.from_user.id in admins_id

        if user is None:
            db.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name, admin)
            args = command.args
            if args and len(args) > 0:
                payload = decode_payload(args)
                if payload:
                    db.update_referals(payload, message.from_user.id)
                    await message.answer(f"🥳 Тебя пригласил: {payload}")
                    await bot.send_message(payload, f"🥳 Прошу внимания, у вас новый реферал: @{message.from_user.username}!")

            await bot.send_sticker(message.from_user.id, "CAACAgIAAxkBAAEMmMhmrfZaUBIXhdd9CtetAAEOp9pL59wAAocVAAI9D1BJ3ptm_dbHo781BA")
            document = FSInputFile('pictures/avatar_group.jpg')
            await message.answer_photo(document, caption="""
👋 Привет! Я - умный бот, который разнообразит ваше времяпровождение на серверах.
👉 Если у тебя есть вопрсы, или предложения, вы можете создать тикет, нажав на кнопку.
⏬ Чтобы я начал работу, меня достаточно добавить на сервер, кнопкой ниже.
                        """, reply_markup=add_to_server)

        if admin:
            await admin_message_start(message)
        else:
            await user_message_start(message)
    except Exception as e:
        if isinstance(e, TypeError) and 'object of type \'NoneType\' has no len()' in str(e):
            logger.error("Error: incorrect payload")
        else:
            logger.error(f"Error in cmd_start: {e}")
