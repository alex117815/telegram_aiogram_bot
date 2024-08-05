from aiogram import Router, types, F
from StatesGroup.admin import *
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from db_handler.db_handler import PostgresHandler
from db_handler.db_server import PostgresHandlerServer
from create_bot import bot
from keyboards.admin_kb import *
from handlers.admin_handlers import admin_message_start
import logging
from aiogram.types import Message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

adm_keyboard = Router()

@adm_keyboard.callback_query(F.data == 'all_users')
async def all_users(callback_query: types.CallbackQuery) -> None:
    try:
        db = PostgresHandler()
        all_users_obj = db.get_all_users()
        users_count = len(all_users_obj)
        await callback_query.message.answer(f'Всего пользователей: {users_count}')
        await callback_query.answer()
    except Exception as e:
        logger.error(e)

@adm_keyboard.callback_query(F.data == 'user_info')
async def user_info(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UserInfoForm.waiting_for_user_id)
    message = await callback_query.message.edit_text('Введите id пользователя:', reply_markup=admin_kb_cancel)
    await state.update_data(message_id=message.message_id, chat_id=message.chat.id)
    await callback_query.answer()

@adm_keyboard.message(UserInfoForm.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext) -> None:
    try:
        user_id = int(message.text)

        data = await state.get_data()
        chat_id = data.get('chat_id')
        message_id = data.get('message_id')
        await message.bot.delete_message(chat_id=chat_id, message_id=message_id)

        if user_id < 0:
            await message.answer('Пожалуйста, введите действительный числовой id пользователя.')
            return

        await state.update_data(user_id=message.text)
        await state.clear()
        db = PostgresHandler()
        user_obj = db.get_user(user_id)
        actions_kb = profile_actions_kb(user_id)
        if user_obj:
            await message.answer(f"""
ℹ️ Имя: {user_obj.name}
🎯 Телеграм: @{user_obj.username} -- {user_obj.id}
🧓 Админ: {"Да" if user_obj.admin else "Нет"}
🎖️ Верефицирован: {"Да" if user_obj.verified else "Нет"}
🎮 Рефрералов: {user_obj.referals}
📆 Дата регестрации: {user_obj.date_reg}
""", reply_markup=actions_kb)
        else:
            await message.answer('Пользователь не найден.')
    except ValueError:
        await message.answer('Пожалуйста, введите действительный числовой id пользователя.')
    except Exception as e:
        logger.error(e)
        await message.answer('Произошла ошибка при получении информации о пользователе.')
        await state.clear()

@adm_keyboard.callback_query(F.data == 'adm_profile')
async def adm_profile(callback_query: types.CallbackQuery) -> None:
    try:
        db = PostgresHandler()
        adm_profile_obj = db.get_admin(callback_query.from_user.id)
        await callback_query.message.edit_text(f"""
❇️ Статус: {adm_profile_obj.status}
ℹ️ Айди: {adm_profile_obj.id}
🕖 Стали админом: {adm_profile_obj.date_start}
""", reply_markup=admin_kb_cancel)
        await callback_query.answer()
    except Exception as e:
        logger.error(e)

@adm_keyboard.callback_query(F.data == 'send_mess')
async def send_mess(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    try:
        can = await helper_check(callback_query.from_user.id)
        if not can:
            await callback_query.message.answer('❌ У вас нет доступа к этой функции.')
            await callback_query.answer()
            return
        await state.set_state(SendMessForm.waiting_for_text)
        message = await callback_query.message.edit_text('↪️ Этап 1. Введите текст для рассылки', reply_markup=admin_kb_cancel)
        await state.update_data(message=message ,message_id=message.message_id, chat_id=message.chat.id)
        await callback_query.answer()
    except Exception as e:
        logger.error(e)

@adm_keyboard.message(SendMessForm.choose)
async def choose_type(message: types.Message, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        chat_id = data.get('chat_id')
        message_id = data.get('message_id')
        try:
            await message.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(e)

        if message.content_type == 'photo':
            photo_id = message.photo[-1].file_id
            await state.update_data(photo=photo_id)
            logger.info(photo_id)

        await state.set_state(SendMessForm.spam)
        msg = await message.answer('↪️ Этап 3. Выберете тип рассылки:', reply_markup=create_spam_type_kb)
        await state.update_data(message_id=msg.message_id, chat_id=msg.chat.id)
    except Exception as e:
        logger.error(e)

@adm_keyboard.message(SendMessForm.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext) -> None:
    try:
        await state.set_state(SendMessForm.choose)

        data = await state.get_data()
        chat_id = data.get('chat_id')
        message_id = data.get('message_id')
        try:
            await message.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(e)

        await state.update_data(text=message.text)
        
        msg = await message.answer(
            f'↪️ Этап 2. Отправьте изображение для рассылки или нажмите "Пропустить", если изображение не требуется',
            reply_markup=admin_kb_skip_or_cancel
        )
        await state.update_data(message=msg, message_id=msg.message_id, chat_id=msg.chat.id)
    except Exception as e:
        logger.error(f"Error in process_text: {e}")
        await message.answer(f'Произошла ошибка при обработке текста. {e}')

@adm_keyboard.callback_query(F.data == "skip_image_spam")
@adm_keyboard.message(SendMessForm.waiting_for_image)
async def process_skip_image(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        chat_id = data.get('chat_id')
        message_id = data.get('message_id')
        try:
            await callback_query.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(e)
        await state.set_state(SendMessForm.choose)
        await state.update_data(image=False)
        await callback_query.answer('Успешно пропустили изображение.')

        await choose_type(callback_query.message, state)
    except Exception as e:
        logger.error(f"Error in process_skip_image: {e}")

@adm_keyboard.callback_query(F.data.startswith('spam_in'))
@adm_keyboard.message(SendMessForm.spam)
async def process_image_or_skip(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    try:
        type_ = str(callback_query.data).replace('spam_in_', '')
        logger.info(callback_query.data)
        logger.info(type_)

        data = await state.get_data()
        text = data.get('text')
        pg = PostgresHandler()
        message_id = data.get('message_id')
        chat_id = data.get('chat_id')
        await callback_query.bot.delete_message(chat_id=chat_id, message_id=message_id)
        pg_server = PostgresHandlerServer()
        image = data.get('photo')
        logger.info(image)

        if type_ == 'bot':
            logger.info("Spam in bot")
            ids_obj = pg.get_all_ids()
            logger.info(pg.get_all_ids())
            for id_ in ids_obj:
                if image != None:
                    await callback_query.message.bot.send_photo(id_, image, caption=text, parse_mode='HTML')
                else:
                    await callback_query.message.bot.send_message(id_, text, parse_mode='HTML')
        else:
            logger.info("Spam in server")
            ids_obj = [f"-{server_id}" for server_id in pg_server.get_all_servers_ids()]
            logger.info(pg_server.get_all_servers_ids())
            for id_ in ids_obj:
                if image != None:
                    await callback_query.message.bot.send_photo(id_, image, caption=text, parse_mode='HTML')
                else:
                    await callback_query.message.bot.send_message(id_, text, parse_mode='HTML')
        logger.info(ids_obj)

        logger.info(type_)
        await state.clear()
        await callback_query.answer()
        await callback_query.message.answer(f'🗣️ Рассылка запущена. Отправлена {len(ids_obj)} {"пользователям" if type_ == "spam_in_bot" else "серверам"}.', reply_markup=ReplyKeyboardRemove())
        await admin_message_start(callback_query.message)
    except Exception as e:
        logger.error(f"error in process_image_or_skip: {e}")
        await callback_query.message.answer('Произошла ошибка при рассылке.', reply_markup=ReplyKeyboardRemove())

async def helper_check(user_id: int) -> None:
    pg = PostgresHandler()
    adm_profile_obj = pg.get_admin(user_id)
    if adm_profile_obj.status == 'helper':
        return False
    else:
        return True

@adm_keyboard.callback_query(F.data == 'add_admin')
async def add_admin(cb: types.CallbackQuery, state: FSMContext) -> None:
    try:
        can = await helper_check(cb.from_user.id)
        if not can:
            return await cb.message.answer(
                'Ваш ранг еще слишком низкий.',
                reply_markup=admin_kb_cancel,
                reply=False
            )
        await state.set_state(AddAdminForm.waiting_for_user_id)
        await cb.message.edit_text(
            "Введите id пользователя:",
            reply_markup=admin_kb_cancel
        )
        await state.update_data(
            message_id=cb.message.message_id,
            chat_id=cb.message.chat.id
        )
        await cb.answer()
    except Exception as e:
        logger.error(e)

@adm_keyboard.message(AddAdminForm.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext) -> None:
    try:
        user_id = int(message.text)
        data = await state.get_data()
        chat_id = data.get('chat_id')
        message_id = data.get('message_id')
        await message.bot.delete_message(chat_id=chat_id, message_id=message_id)

        if user_id < 0:
            await message.answer('Пожалуйста, введите действительный числовой id пользователя.')
            return

        await state.update_data(user_id=message.text)
        await state.clear()
        db = PostgresHandler()
        user_obj = db.get_user(user_id)
        if user_obj:
            db.add_admin(user_id)
            admin = user_obj.admin
            if admin:
                await message.answer(f'Пользователь {user_obj.name} уже является администратором.')
                return
            await message.answer(f'Пользователь {user_obj.name} добавлен в администраторы.')
            await bot.send_message(user_id, 'Ты стал администратором. Тебя добавил: @' + message.from_user.username)
        else:
            await message.answer('Пользователь не найден.')
    except ValueError:
        await message.answer('Пожалуйста, введите действительный числовой id пользователя.')
    except Exception as e:
        logger.error(f"Ошибка в process_user_id: {e}")

@adm_keyboard.callback_query(F.data == 'del_admin')
async def delete_admin(cb: types.CallbackQuery, state: FSMContext) -> None:
    try:
        can = await helper_check(cb.from_user.id)
        if not can:
            await cb.message.answer('Ваш ранг еще слишком низкий.')
            await cb.answer()
            return
        await state.set_state(DelAdminForm.waiting_for_user_id)
        message = await cb.message.edit_text("Введите id пользователя:", reply_markup=admin_kb_cancel)
        await state.update_data(message_id=message.message_id, chat_id=message.chat.id)
        await cb.answer()
    except Exception as e:
        logger.error(e)

@adm_keyboard.message(DelAdminForm.waiting_for_user_id)
async def process_user_id_del_adm(message: types.Message, state: FSMContext) -> None:
    try:
        user_id = int(message.text)
        data = await state.get_data()
        chat_id = data.get('chat_id')
        message_id = data.get('message_id')
        await message.bot.delete_message(chat_id=chat_id, message_id=message_id)

        if user_id < 0:
            await message.answer('Пожалуйста, введите действительный числовой id пользователя.')
            return

        await state.update_data(user_id=message.text)
        await state.clear()
        db = PostgresHandler()
        user_obj = db.get_user(user_id)
        if user_obj:
            db.delete_admin(user_id)
            admin = user_obj.admin
            if not admin:
                await message.answer(f'Пользователь {user_obj.name} не админ.')
                return
            await message.answer(f'Пользователь {user_obj.name} удален из админов.')
            await bot.send_message(user_id, 'Больше ты не админ. Тебя удалил: @' + message.from_user.username)
        else:
            await message.answer('Пользователь не найден.')
    except ValueError:
        await message.answer('Пожалуйста, введите действительный числовой id пользователя.')
    except Exception as e:
        logger.error(e)

@adm_keyboard.callback_query(F.data == 'tickets')
async def tickets_list(cb: types.CallbackQuery) -> None:
    try:
        db = PostgresHandler()
        all_tickets = db.get_all_tickets()
        open_tickets = db.search_ticket_by_admin_info(cb.from_user.id)
        if all_tickets:
            tickets_kb = create_tickets_kb(all_tickets)
            await cb.message.answer(f'📜 Всего заявок: {len(all_tickets)}\n⚠️ Давайте-же поработаем!\n⬇️ Чтобы начать разбирать жалобу, просто нажмите на нее ниже', reply_markup=tickets_kb)
        elif open_tickets:
            open_kb = create_tickets_kb(open_tickets)
            await cb.message.answer(f"📝 Открытые заявки: {len(open_tickets)}\n📜 Всего заявок: {f'{len(all_tickets)}' if all_tickets else '0'}", reply_markup=open_kb)
        else:
            await cb.message.answer('Заявок нет, отдыхайте.')
        await cb.answer()

    except Exception as e:
        logger.error(e)

@adm_keyboard.callback_query(F.data.startswith('Ticket'))
async def ticket_details(cb: types.CallbackQuery) -> None:
    try:
        ticket_id = int(cb.data.replace('Ticket', ''))
        db = PostgresHandler()
        ticket = db.get_ticket(ticket_id)
        ticket_actions_kb = create_ticket_actions_kb(ticket_id)
        opnd_tickets_kb = open_ticket_actions_kb(ticket_id)
        if ticket:
            try:
                ticket_number = len(ticket.text)
                if ticket_number < 30:
                    complexity = '🟢 Легкая'
                elif ticket_number < 100:
                    complexity = '🟡 Средняя'
                else:
                    complexity = '🔴 Сложная.. удачки'
            except Exception as e:
                complexity = '❓ Неопределённый'
                logging.error(f"error in complexity: {e}")

            if ticket.status == "Accepted" and ticket.admin_id == cb.from_user.id:
                ticket_info = (
                    f"ℹ️ Айди тикета: <b>{ticket.ticket_id}</b>\n"
                    f"📄 Текст обращения: <b>{ticket.text}</b>\n"
                    f"⚠️ Может, вы уже решите этот тикет?\n"
                )
                await cb.message.answer(ticket_info, parse_mode='HTML', reply_markup=opnd_tickets_kb)
                db.add_view(ticket_id)
            else:
                ticket_info = (
                    f"ℹ️ Айди тикета: <b>{ticket.ticket_id}</b>\n"
                    f"📥 Статус: {ticket.status}\n"
                    f"⛔ Сложность: <b>{complexity}</b>\n"
                    f"📄 Текст обращения: <b>{ticket.text}</b>\n"
                    f"📸 Фото: <b>{'Да' if ticket.photo else 'Не прикреплено.'}</b>\n"
                    f"📅 Дата создания: {ticket.date}\n"
                    f"👤 Айди пользователя: {ticket.user_id}\n"
                    f"🤴 Айди админа: {f'{ticket.admin_id}' if ticket.admin_id else 'Еще никто не разобрал жалобу'}\n"
                    f"👀 Заявку посмотрели: <b>{ticket.views}</b> раз."
                )
                await cb.message.answer(ticket_info, parse_mode='HTML', reply_markup=ticket_actions_kb)
                db.add_view(ticket_id)
        else:
            await cb.message.answer(f'Заявка с ID {ticket_id} не найдена.')
        await cb.answer()

    except Exception as e:
        logger.error(f"Error fetching ticket details: {e}")
        await cb.message.answer("Произошла ошибка при получении информации о заявке.")

@adm_keyboard.callback_query(F.data == 'back_to_ticket_list')
async def back_to_ticket_list(cb: types.CallbackQuery) -> None:
    try:
        await cb.message.answer('✅ Вы вернулись в список заявок', reply_markup=ReplyKeyboardRemove())
        await tickets_list(cb)

    except Exception as e:
        logger.error(f'Error in back_to_ticket_list: {e}')

@adm_keyboard.callback_query(F.data.startswith('reject_ticket='))
async def reject_ticket(cb: types.CallbackQuery, state: FSMContext) -> None:
    try:
        ticket_id = int(cb.data.replace('reject_ticket=', ''))
        db = PostgresHandler()
        ticket = db.get_ticket(ticket_id)
        await cb.message.answer(f'✅ Заявка с id {ticket_id} отклонена, и была удалена из базы данных.', reply_markup=ReplyKeyboardRemove())
        await bot.send_sticker(cb.from_user.id, 'CAACAgIAAxkBAAEMjv1mp3Ee8qrHaGaO5o6UdP-3dCQDOwACFSAAAsqUKEhEjgiX0nhf7DUE')
        await bot.send_message(ticket.user_id, f'❌ Вашу заявку закрыли!\n🤴 Админ: {cb.from_user.full_name}.\n📋 Текст вашей заявки: {ticket.text}', reply_markup=ReplyKeyboardRemove())
        await bot.send_sticker(ticket.user_id, 'CAACAgIAAxkBAAEMjvtmp3C-nv61kS_YwhffURc2PmcAAWkAAiQfAAJo1yBIsRtMqAOkNgk1BA')
        
        db.del_ticket(ticket_id)
        await cb.answer()
        await state.clear()

    except Exception as e:
        logger.error(f'Error rejecting ticket: {e}\n{ticket_id}')
        db = PostgresHandler()
        db.del_ticket(ticket_id)
        await cb.answer(f"Произошла ошибка при отклонении заявки. Заявка была удаленна.")
        await cb.answer()

@adm_keyboard.callback_query(F.data.startswith('accept_ticket='))
async def accept_ticket(cb: types.CallbackQuery, state: FSMContext) -> None:
    try:
        ticket_id = int(cb.data.replace('accept_ticket=', ''))
        pg = PostgresHandler()
        ticket = pg.get_ticket(ticket_id)
        ticket_kb = stop_tickets_kb(ticket_id)

        #Database
        db = PostgresHandler()
        db.edit_ticket_status_and_admin_id(ticket_id, 'Accepted', cb.from_user.id)
        #Админу
        await cb.message.answer(f'✅ Заявка с id {ticket.ticket_id} принята! Напишите сообщение человеку, или отмените через клавиатуру.', reply_markup=ticket_kb)
        await bot.send_sticker(cb.from_user.id, 'CAACAgIAAxkBAAEMjv1mp3Ee8qrHaGaO5o6UdP-3dCQDOwACFSAAAsqUKEhEjgiX0nhf7DUE')

        #Кто подовал заявку
        await bot.send_message(ticket.user_id, f'✅ Ваша заявка принята!\n🤴 Админ: {cb.from_user.full_name}.\n📋 Текст вашей заявки: {ticket.text}', reply_markup=ticket_kb)
        await bot.send_sticker(ticket.user_id, 'CAACAgIAAxkBAAEMjvtmp3C-nv61kS_YwhffURc2PmcAAWkAAiQfAAJo1yBIsRtMqAOkNgk1BA')
        
        await state.update_data(ticket_id=ticket_id, admin_id=ticket.admin_id, user_id=ticket.user_id)
        await state.set_state(OnlineTicket.admin_send_messages)
        await cb.answer()
        logger.info(f'Admin {cb.from_user.full_name} accepted ticket {ticket_id}, user_Id: {ticket.user_id}')
    except Exception as e:
        logger.error(f'Error in accept_ticket: {e}')


@adm_keyboard.message(OnlineTicket.admin_send_messages)
async def admin_send_messages(msg: Message, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        admin_id, user_id, ticket_id = data.get('admin_id'), data.get('user_id'), data.get('ticket_id')
        logger.info(f"{user_id} {admin_id} {ticket_id}")

        if not ticket_id:
            return
        
        pg = PostgresHandler()
        ticket = pg.get_ticket(ticket_id)

        if not ticket:
            return
        
        if not ticket.status == "Accepted":
            return

        sender_id = msg.from_user.id
        message = msg.text

        if message in ("❌ Остановить диалог", "✅ Продолжить диалог"):
            func = stop_ticket_messages if message == "❌ Остановить диалог" else continue_ticket_messages
            await func(msg, state)
            return
        
        if sender_id == user_id:
            if admin_id is None:
                admin_id = ticket.admin_id
                await state.update_data(admin_id=ticket.admin_id)

        else:
            admin_id = sender_id

        text = f'📝 Сообщение от {"пользователя" if sender_id == user_id else "админа"}: <b>{message}</b>'
        if sender_id == user_id:
            await bot.send_message(admin_id, text, parse_mode='HTML')
        else:
            await bot.send_message(user_id, text, parse_mode='HTML')
    except Exception as e:
        logger.error(f'Error in admin_send_messages: {e}')
        await msg.answer('❌ Ошибка при отправке сообщения. Пожалуйста, закройте данный тикет.')
        pg.del_ticket(ticket_id)
        await state.clear()

@adm_keyboard.message(F.text == "❌ Остановить диалог")
async def stop_ticket_messages(message: Message, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        ticket_id = data.get('ticket_id')

        if ticket_id is None:
            return

        continue_dialoge = continute_tickets_kb(ticket_id)
        await state.set_state(OnlineTicket.wait)
        await message.answer(f'📵 Диалог остановлен. Теперь сообщения в чате не будут отправлены пользователю.', reply_markup=continue_dialoge)
    except Exception as e:
        logger.error(f'Error in stop_ticket_messages: {e}')

@adm_keyboard.message(F.text == "✅ Продолжить диалог")
async def continue_ticket_messages(message: Message, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        ticket_id = data.get('ticket_id')
        if ticket_id is None:
            return

        keyboard = stop_tickets_kb(ticket_id)

        await state.set_state(OnlineTicket.admin_send_messages)
        await message.answer(f'🗣️ Диалог продолжен. Теперь сообщения в чате будут отправлены пользователю.', reply_markup=keyboard)
    except Exception as e:
        logger.error(f'Error in continue_ticket_messages: {e}')

@adm_keyboard.callback_query(F.data.startswith('message_ticket='))
async def message_ticket(cb: types.CallbackQuery, state: FSMContext) -> None:
    try:
        ticket_id = int(cb.data.replace('message_ticket=', ''))
        ticket = PostgresHandler().get_ticket(ticket_id)

        await state.update_data(ticket_id=ticket_id, user_id=ticket.user_id)
        await state.set_state(OnlineTicket.admin_send_messages)
        await cb.message.answer('📝 Напишите сообщение человеку:')
        await cb.answer()
    except Exception as e:
        logger.error(f'Error in message_ticket: {e}')

@adm_keyboard.callback_query(F.data == 'Statistico')
async def statistico(cb: types.CallbackQuery) -> None:
    try:
        can = await helper_check(cb.from_user.id)
        if not can:
            await cb.message.answer('❌ У вас нет прав для использования этой команды')
            await cb.answer()
            return

        db = PostgresHandler()
        db_group = PostgresHandlerServer()
        tickets = db.get_all_tickets()
        users = db.get_all_users()
        locations = db.get_populars_locations()
        admins = db.get_all_admins()
        all_servers = db_group.get_all_servers()
        total_server_users = db_group.get_total_users()

        tickets_count = len(tickets) if tickets is not None else "Не удалось найти"
        users_count = len(users) if users is not None else "Не удалось найти"
        admins_count = len(admins) if admins is not None else "Не удалось найти"
        all_servers = all_servers if all_servers is not None else "Не удалось найти"
        total_server_users = total_server_users if total_server_users is not None else "Не удалось найти"

        await cb.message.answer(f"""
📊 Статистика:
👥 Пользователей в боте: {users_count}
🛡️ Всего серверов: {all_servers}
🫅 Всего пользователей на серверах: {total_server_users}
📫 Открытых тикетов: {tickets_count}
👷‍♀️ Администраторов: {admins_count}
🗺️ Самые популярные места: {locations}
""")
        await cb.answer()
    except Exception as e:
        logger.error(f'Error in statistico: {e}')

@adm_keyboard.callback_query(F.data.startswith('ban_profile='))
async def ban_profile(cb: types.CallbackQuery) -> None:
    try:
        can = await helper_check(cb.from_user.id)
        if not can:
            await cb.message.answer('❌ У вас нет прав для использования этой команды')
            await cb.answer()
            return
        
        user_id = int(cb.data.replace('ban_profile=', ''))
        db = PostgresHandler()
        db.ban_profile(user_id)

        unban_kb = unban_profile_kb(user_id)
        await cb.message.answer(f'🟢 Пользователь {user_id} был забанен.', reply_markup=unban_kb)
        await cb.answer()
    except Exception as e:
        logger.error(f'Error in ban_profile: {e}')

@adm_keyboard.callback_query(F.data.startswith('unban_profile='))
async def unban_profile(cb: types.CallbackQuery) -> None:
    try:
        can = await helper_check(cb.from_user.id)
        if not can:
            await cb.message.answer('❌ У вас нет прав для использования этой команды')
            await cb.answer()
            return

        user_id = int(cb.data.replace('unban_profile=', ''))
        db = PostgresHandler()
        db.unban_profile(user_id)

        await cb.message.answer(f'🔴 Пользователь {user_id} был разбанен.')
        await cb.answer()

    except Exception as e:
        logger.error(f'Error in unban_profile: {e}')

@adm_keyboard.callback_query(F.data.startswith('message_profile='))
async def message_profile(cb: types.CallbackQuery, state: FSMContext) -> None:
    try:
        can = await helper_check(cb.from_user.id)
        if not can:
            await cb.message.answer('❌ У вас нет прав для использования этой команды')
            await cb.answer()
            return
        
        user_id = int(cb.data.replace('message_profile=', ''))
        await state.update_data(user_id=user_id)
        await state.set_state(SendMessageProfile.wait)

        await cb.message.answer('📝 Напишите сообщение человеку:')
        await cb.answer()
    except Exception as e:
        logger.error(f'Error in message_profile: {e}')

@adm_keyboard.message(SendMessageProfile.wait)
async def send_message_profile(msg: types.Message, state: FSMContext) -> None:
    try:

        data = await state.get_data()
        user_id = data.get('user_id')
        text = msg.text

        await bot.send_message(user_id, f"👑 Поступило сообщение от администратора: {text}")
        await bot.send_sticker(user_id, 'CAACAgIAAxkBAAEMkJBmqMmKt-BFFppX7vHA1qhwYaYv1QACzBgAAntYUEmwTZrmztcawjUE')
        await msg.reply('✅ Сообщение было отправлено')
        await state.clear()
    except Exception as e:
        logger.error(f'Error in send_message_profile: {e}')

@adm_keyboard.callback_query(F.data == 'cancel')
async def cancel(cb: types.CallbackQuery) -> None:
    try:
        await admin_message_start(cb.message)
        await cb.answer()
    except Exception as e:
        logger.error(f'Error in cancel: {e}')