from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from StatesGroup.admin import OnlineTicket
from db_handler.db_handler import PostgresHandler
from keyboards.user_kb import *
from keyboards.admin_kb import *
from create_bot import bot
from aiogram.utils.deep_linking import create_start_link
import logging
from StatesGroup.user import *
from StatesGroup.admin import *
import phonenumbers
from phonenumbers.phonenumberutil import (
    region_code_for_country_code,
)
from handlers.user_handlers import user_message_start

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

usr_keyboard = Router()

@usr_keyboard.callback_query(F.data == 'profile')
async def profile(callback_query: types.CallbackQuery) -> None:
    try:
        db = PostgresHandler()
        user_obj = db.get_user(callback_query.from_user.id)
        link = db.get_referal_link(callback_query.from_user.id)

        if link is None:
            link = await create_start_link(bot, callback_query.from_user.id, encode=True) 
            db.set_referal_link(callback_query.from_user.id, link)

        if user_obj:
            reply_markup = verified_kb if not user_obj.verified else None
            await callback_query.message.answer( 
                f"""
👨 Профиль: {user_obj.name} - @{user_obj.username}
🆔 Айди: {user_obj.id}
⚜️ Администратор: {"Да" if user_obj.admin else "Нет"}
📶 Приглашено рефералов: {user_obj.referals}
📆 Дата регистрации: {user_obj.date_reg}
👤 Верефицирован: {"✅" if user_obj.verified else "❌"}

🔗 Ссылка для друга: {link}
""", reply_markup=reply_markup)

        await callback_query.answer()
    except Exception as e:
        logger.error(e)

@usr_keyboard.callback_query(F.data == 'write_ticket')
async def write_ticket(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    try:
        pg = PostgresHandler()
        open_tickets = pg.search_ticket_by_user_id(callback_query.from_user.id)
        if open_tickets:
            open_ticket = open_tickets[0]
            await callback_query.message.answer(f'📝 Ваше обращение уже было отправлено. Админы разберут его как только смогут.\n\nℹ️ ID: {open_ticket.ticket_id}\n📋 Текст обращения: {open_ticket.text}')
            await callback_query.answer()
            return

        await state.set_state(WriteTicket.waiting_for_text)
        await callback_query.message.answer('📝 Напишите ваш вопрос:', reply_markup=cancel_kb_user) 
        await callback_query.answer()
    except Exception as e:
        logger.error(e)

@usr_keyboard.callback_query(F.data == 'cancel_user_kb')
async def cancel(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    try:
        await state.clear()
        await callback_query.message.answer('❌ Отменено', reply_markup=ReplyKeyboardRemove())
        await callback_query.answer()

        await user_message_start(callback_query.message)
    except Exception as e:
        logger.error(e)

@usr_keyboard.message(WriteTicket.waiting_for_text)
async def process_text(
    message: types.Message, 
    state: FSMContext
) -> None:
    await state.update_data(text=message.text)
    await state.set_state(WriteTicket.picture)
    await message.answer(
        '📸 Прикрепите изображение, либо пропустите кнопкой ниже.', 
        reply_markup=skip_or_cancel
    )
    
@usr_keyboard.message(WriteTicket.picture)
async def process_picture(message: types.Message, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        text = data.get('text')

        pg = PostgresHandler()
        if message.text == '⏭ Пропустить':
            pg.new_ticket(message.from_user.id, text) 
            ticket_obj = pg.search_ticket_by_user_id(message.from_user.id)
        elif message.text == '❌ Отмена':
            await message.answer('Отменено', reply_markup=ReplyKeyboardRemove())
            await state.clear()
            return
        elif message.content_type == 'photo':
            picture_file_id = message.photo[-1].file_id 
            await state.update_data(picture=picture_file_id)
            logger.info(picture_file_id)
            pg.new_ticket(message.from_user.id, text, picture_file_id)
            ticket_obj = pg.search_ticket_by_user_id(message.from_user.id)
            await bot.send_photo(message.from_user.id, picture_file_id, caption=text)

        await state.update_data(user_id=message.from_user.id, ticket_id=ticket_obj[0].ticket_id)
        await message.answer('✅ Тикет создан. Ожидайте ответа.', reply_markup=ReplyKeyboardRemove())
        await state.set_state(OnlineTicket.admin_send_messages)
    except Exception as e:
        logger.error(e)

@usr_keyboard.message(F.contact)
async def get_verified(message: types.Message, state: FSMContext) -> None:
    try:
        db = PostgresHandler()
        user_obj = db.get_user(message.from_user.id)
        if user_obj.verified:
            await message.answer('❌ Ваш аккаунт уже верифицирован.')
            return
        
        pn = phonenumbers.parse(message.contact.phone_number)
        location = region_code_for_country_code(pn.country_code)
        if location:
            location = location
        
        await message.answer(f"""
✅ Верификация прошла успешно. Теперь вы можете писать обращения в нашем боте.
🧑‍💻 {message.contact.phone_number}
🌎 Расположение: {location}
""", reply_markup=cancel_kb_user)
        await message.answer('✅ Теперь ваш статус верифицирован.', reply_markup=ReplyKeyboardRemove())
        
        db.set_verified(message.from_user.id)
        logger.info(message.contact.phone_number)
        db.set_location(message.from_user.id, location)
        
    except Exception as e:
        logger.error(f"Error in get_verified: {e}")