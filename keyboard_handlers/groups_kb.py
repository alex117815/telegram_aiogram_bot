from aiogram import Router, types, F
import logging
from StatesGroup.group import *
from create_bot import bot
from keyboards.gropus_kb import *
from db_handler.db_server import PostgresHandlerServer
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, Command
from aiogram.filters.chat_member_updated import *
from aiogram.types.input_file import FSInputFile
from aiogram.enums import ChatType
import time
import asyncio
import re
from datetime import datetime, timedelta
from aiogram.fsm.context import FSMContext
from enums.group_enum import EightBallReply
from check_swear import SwearingCheck
import aiohttp
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
sch = SwearingCheck()

class ChatTypeFilter(Filter):
    def __init__(self, chat_type: str | list):
        self.chat_type = chat_type

    async def __call__(self, message: types.Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type

group_router = Router()
group_router.message.filter(
    ChatTypeFilter(chat_type=['supergroup', 'group'])
)

@group_router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def new_user(event: types.ChatMemberUpdated, state: FSMContext) -> None:
    try:
        if not event.chat or not event.new_chat_member:
            logger.error("Error in new_user: event.chat or event.new_chat_member is None")
            return

        pg = PostgresHandlerServer()
        server_id = str(event.chat.id).replace('-', '')
        server = pg.get_server_settings(int(server_id))
        if not server or not server.welcome_users:
            return

        approve_kb = approve_new_user(event.chat.id, event.new_chat_member.user.id)
        user = pg.get_user(int(server_id), event.new_chat_member.user.id)
        if not user:
            pg.add_user(int(server_id), event.new_chat_member.user.id)

        await bot.restrict_chat_member(
            chat_id=event.chat.id,
            user_id=event.new_chat_member.user.id,
            permissions=types.ChatPermissions(can_send_messages=False)
        )
        msg = await event.answer(
            f'😇 У нас новый пользователь!\n👋 Привет, @{event.new_chat_member.user.username}!\n⏬ Подтверди что ты не бот, и нажми на кнопку ниже',
            reply_markup=approve_kb
        )
        await state.update_data(
            chat_id=event.chat.id,
            new_chat_member_id=event.new_chat_member.user.id,
            message_id=msg.message_id
        )
        await state.set_state(NewUser.step_one)
    except Exception as e:
        logger.exception(f"Error in new_user: {e}")
        raise


@group_router.chat_member(
    ChatMemberUpdatedFilter(
        IS_MEMBER >> IS_NOT_MEMBER
    )
)
async def user_leave(event: ChatMemberUpdated):
    try:

        pg = PostgresHandlerServer()
        server_id = str(event.chat.id).replace('-', '')
        server = pg.get_server_settings(int(server_id))

        if server is None:
            pg.create_table(int(server_id))
            server = pg.get_server_settings(int(server_id))

        if server and server.goodbye_users:
            pg.del_user(int(server_id), event.old_chat_member.user.id)
            await event.answer(f'😢 Пользователь @{event.old_chat_member.user.username} покинул нас, больше он не с нами.')
    except Exception as e:
        logger.error(f"Error in user_leave: {e}")

@group_router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    try:

        admins = await event.chat.get_administrators()
        if not admins:
            logger.error("Error in on_user_join: event.chat.get_administrators() returned an empty list")
            admins = []

        admins = [admin.user.username for admin in admins if admin.user is not None]
        logger.info(f'Admins in chat {event.chat.title}: {admins}')

        document = FSInputFile('pictures/group_join.jpg')

        try:
            await event.answer_photo(
                photo=document,
                caption=f"""
💫 Привет, меня зовут <b>Keaxy</b>, и я сделаю ваш канал увлекательнее.

🫅 Администраторы на сервере:
@{', @'.join(map(str, admins))}

<b>🎩 Написав "/" ты можешь увидеть мои команды!</b>
""", parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error in on_user_join: event.answer_photo failed with error {e}")

        chat_id = str(event.chat.id).replace('-', '')
        if chat_id is None:
            logger.error("Error in on_user_join: chat_id is None")
            return

        pg = PostgresHandlerServer()

        if not pg.check_chat_id(int(chat_id)):
            pg.create_table(int(chat_id))

        try:
            total_users = await event.chat.get_member_count()
        except Exception as e:
            logger.error(f"Error in on_user_join: event.chat.get_member_count failed with error {e}")
            return
        pg.update_total_users(int(chat_id), total_users)
        logger.info(f'Created table for chat {event.chat.title}')

        try:
            await set_default_commands()
        except Exception as e:
            logger.error(f"Error in on_user_join: set_default_commands failed with error {e}")

    except Exception as e:
        logger.error(f"Error in on_user_join: {e}")

async def set_default_commands():
    user_commands = [
        types.BotCommand(command="start", description="Старт"),
        types.BotCommand(command="profile", description="Мой профиль"),
        types.BotCommand(command="dice", description="Кинуть кубик"),
        types.BotCommand(command="ask", description="Спросить AI"),
        types.BotCommand(command="8ball", description="Спросить шарик"),
        types.BotCommand(command="settings", description="Настройки сервера"),
        types.BotCommand(command="couple", description="Пара дня"),
        types.BotCommand(command="top_karma", description="Топ пользователей по карме"),
    ]

    admin_commands = [
        types.BotCommand(command="users", description="Информация о пользователях"),
        types.BotCommand(command="mute", description="Замутить пользователя"),
        types.BotCommand(command="kick", description="Кикнуть пользователя"),
        types.BotCommand(command="ban", description="Забанить пользователя"),
    ]

    await bot.set_my_commands(user_commands, scope=types.BotCommandScopeAllGroupChats())

    #admins
    await bot.set_my_commands(admin_commands, scope=types.BotCommandScopeAllChatAdministrators())
    await bot.set_my_commands(user_commands, scope=types.BotCommandScopeAllChatAdministrators())

async def check_user_in_database(message: types.Message):
    try:
        assert message is not None
        assert message.chat is not None
        assert message.from_user is not None

        pg = PostgresHandlerServer()
        chat_id = str(message.chat.id).replace('-', '')
        logger.info(f'chat_id: {chat_id}, message.from_user.id: {message.from_user.id}')

        user = pg.get_user(int(chat_id), message.from_user.id)
        
        if user is None:
            logger.info(f'User {message.from_user.id} not in database')

            admins = await message.chat.get_administrators()
            assert admins is not None
            admins = [admin.user.id for admin in admins]
            logger.info(f'Admins in chat {message.chat.title}: {admins}')

            if message.from_user.id in admins:
                logger.info(f'User {message.from_user.id} added to database by admin')

                pg.add_user(int(chat_id), message.from_user.id, message.from_user.username, admin=True)
            else:
                logger.info(f'User {message.from_user.id} added to database by user')

                pg.add_user(int(chat_id), message.from_user.id, message.from_user.username)
    except AssertionError as e:
        logger.error(f"Error in check_user_in_database: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in check_user_in_database: {e}")

async def check_supergroup(message: types.Message):
    try:
        chat = message.chat
        if chat is None:
            raise ValueError("Chat is None")
        chat_typ = chat.type
        if chat_typ != ChatType.SUPERGROUP:
            logger.info(f'chat_type is not supergroup: {chat_typ}')
            return False
        return True
    except ValueError as e:
        logger.error(f"Error in check_supergroup: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in check_supergroup: {e}")

async def admin_check(message: types.Message) -> bool:
    try:
        assert message is not None
        assert message.chat is not None
        assert message.from_user is not None

        admins = [admin.user.id for admin in await message.chat.get_administrators()]
        if admins is None:
            return False
        pg = PostgresHandlerServer()
        chat_id = str(message.chat.id).replace('-', '')
        if chat_id is None:
            return False
        adm_profile_obj = pg.get_user(int(chat_id), message.from_user.id)
        if adm_profile_obj and adm_profile_obj.admin:
            return True
        if adm_profile_obj is None:
            if message.from_user.id in admins:
                pg.add_user(int(chat_id), message.from_user.id, message.from_user.username, admin=True)
                return True
            else:
                pg.add_user(int(chat_id), message.from_user.id, message.from_user.username, admin=False)
        return False
    except AssertionError as e:
        logger.error(f"Error in admin_check: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in admin_check: {e}")

@group_router.message(F.text == "Профиль")
async def group_message_dice(message: types.Message):
    try:
        await group_profile(message)
    except Exception as e:
        logger.error(f"Error in group_message_dice: {e}")

@group_router.message(Command('profile'))
async def group_profile(message: types.Message):
    try:
        assert message is not None
        assert message.chat is not None
        assert message.from_user is not None

        await check_user_in_database(message)
        pg = PostgresHandlerServer()
        chat_id = str(message.chat.id).replace('-', '')

        if chat_id is None or message.from_user.id is None:
            raise ValueError("chat_id or user_id is None")

        user = pg.get_user(int(chat_id), message.from_user.id)

        if user is not None:
            user_info = f"""
👨 Профиль: {message.from_user.id} - @{message.from_user.username}
🆔 Айди: {user.user_id}
👥 Админ: {"Да" if user.admin else "Нет"}
⏰ Дата регестрации: {user.date_start}
♻️ Репутация: {user.respect}
_
⏱️ Данные обновляются каждые 10 минут.
            """
            await message.answer(user_info)

        else:
            await message.answer('Тебя еще нет в базе данных, подожди, добавляем тебя..')

    except (AssertionError, ValueError) as e:
        logger.error(f"Error in group_profile: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in group_profile: {e}")

@group_router.message(F.text == "Кубик")
async def group_message_dice(message: types.Message):
    try:
        await group_dice(message)
    except Exception as e:
        logger.error(f"Error in group_message_dice: {e}")

@group_router.message(Command('dice'))
async def group_dice(message: types.Message):
    try:
        await check_user_in_database(message)
        await message.answer_dice(emoji='🎲')
    except Exception as e:
        logger.error(f"Error in group_dice: {e}")

@group_router.message(Command('mute'))
async def group_mute(message: types.Message):
    try:
        confirm = await check_supergroup(message)
        if not confirm:
            return await message.answer("🚷 Эта команда может быть использована только в супергрупе")
        
        await check_user_in_database(message)
        if not await admin_check(message): 
            return await message.answer("📛 Только администраторы могут использовать эту команду")

        if not message.reply_to_message:
            return await message.answer("📛 Эта команда должна быть ответом на сообщение пользователя, которого вы хотите замутить")

        target_user = message.reply_to_message.from_user

        text = message.text
        match = re.match(r'^/mute (\d+)([dhmsy]) ?(.*)?$', text)
        if not match:
            return await message.answer("🚷 Неверно введена команда, пример: /mute 3h [причина]\ns - секунды\nh - часы\nd - дни\nИ так далее")

        time_value = int(match.group(1))
        time_unit = match.group(2)
        reason = match.group(3) or 'Не указано'
        logger.info(f"Time value: {time_value}, time unit: {time_unit}, reason: {reason}")

        time_units = {
            'd': 86400,
            'h': 3600,
            'm': 60,
            's': 1,
            'y': 31536000
        }

        time_in_seconds = time_value * time_units.get(time_unit, 1)

        if time_in_seconds < 30:
            time_in_seconds = 30
        elif time_in_seconds > 31536000:
            time_in_seconds = 31536000

        mute_kb = user_mute_kb(target_user.id)

        logger.info(f"Мутим юзера {target_user.id} на {time_in_seconds} секунд по причине: {reason}")
        await bot.restrict_chat_member(message.chat.id, target_user.id, until_date=time.time() + time_in_seconds, permissions=types.ChatPermissions(can_send_messages=False))
        await message.answer(f"✅ Пользователь <b>{target_user.username}</b> был замьючен на <b>{time_in_seconds}</b> секунд\nПричина: <b>{reason}</b>.\n⏳ Размут будет в: <b>{datetime.fromtimestamp(time.time() + time_in_seconds)}</b>", reply_markup=mute_kb, parse_mode='HTML')
        await message.reply_to_message.delete()

    except Exception as e:
        logger.error(f"Error in group_mute: {e}")

@group_router.callback_query(F.data.startswith('unmute_user='))
async def group_unmute_user(cb: types.CallbackQuery):
    try:
        confirm = await check_supergroup(cb.message)
        if not confirm:
            return await cb.message.answer("🚷 Эта команда может быть использована только в супергрупе")
        
        await check_user_in_database(cb.message)
        if not await admin_check(cb.message):
            return await cb.answer("❌ У вас нет прав для использования этой команды")

        user_id = int(cb.data.replace('unmute_user=', ''))
        if user_id == cb.from_user.id:
            return await cb.answer("❌ Вы не можете размутить себя же!)")

        logger.info(f"Размутим юзера {user_id}")

        await bot.restrict_chat_member(cb.message.chat.id, user_id, permissions=types.ChatPermissions(can_send_messages=True))
        await cb.message.answer(f"🗣️ Пользователь {user_id} был размьючен.")
        await cb.answer("🗣️ Пользователь размьючен")
        await cb.message.delete()
        await cb.answer()

    except Exception as e:
        logger.error(f"Error in group_unmute_user: {e}")

@group_router.message(Command('users'))
async def group_users(message: types.Message):
    try:
        admin = await admin_check(message)

        if not admin:
            return await message.answer("📛 Только администраторы могут использовать эту команду")

        await check_user_in_database(message)
        server_id = str(message.chat.id).replace('-', '')
        users_kb = all_users_kb(int(server_id))
        await message.answer("👥 Выбери пользователя:", reply_markup=users_kb)
    except Exception as e:
        logger.error(f"Error in group_play: {e}")

@group_router.callback_query(F.data.startswith('NextPage='))
async def group_next_page(cb: types.CallbackQuery):
    try:
        page_num = int(cb.data.replace('NextPage=', ''))
        keyboard = all_users_kb(page_num)

        await cb.message.edit_reply_markup(reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in group_next_page: {e}")

@group_router.callback_query(F.data.startswith('User_'))
async def group_user_info(cb: types.CallbackQuery):
    try:
        pg = PostgresHandlerServer()
        admin = await admin_check(cb.message)
        if not admin:
            return await cb.message.answer("📛 Только администраторы могут использовать эту команду")
        user_id = int(cb.data.replace('User_', ''))
        logger.info(user_id)
        pg = PostgresHandlerServer()
        server_id = str(cb.message.chat.id).replace('-', '')
        user_obj = pg.get_user(int(server_id), user_id)

        if not user_obj:
            return await cb.message.answer("❌ Пользователь не найден")
        
        await cb.message.answer(f"""
👤 Пользователь: <b>@{user_obj.username}</b>
ℹ️ ID: <b>{user_obj.user_id}</b>
😎 Админ: <b>{"Да" if user_obj.admin else "Нет"}</b>
📅 Дата регистрации: <b>{user_obj.date_start}</b>
♻️ Респекты пользователя: <b>{user_obj.respect}</b>
""", parse_mode='HTML')
        await cb.answer()

    except Exception as e:
        logger.error(f"Error in group_user_info: {e}")

@group_router.message(Command('kick'))
async def group_kick(message: types.Message):
    try:
        admin = await admin_check(message)
        if not admin:
            return await message.answer("📛 Только администраторы могут использовать эту команду")

        await check_user_in_database(message)
        
        target_user = message.reply_to_message.from_user
        if not target_user:
            return await message.answer("❌ Пользователь не найден, ответьте на сообщение пользователя, которого хотите кикнуть.")

        await message.chat.ban(user_id=target_user.id)
        await message.chat.unban(user_id=target_user.id)

        await message.answer(f"🐷 Пользователь @{target_user.username} был кикнут!\n🚨 Больше ему тут не рады.")
        await message.reply_to_message.delete()
    except Exception as e:
        logger.error(f"Error in group_kick: {e}")

@group_router.message(Command('ban'))
async def group_ban(message: types.Message):
    try:
        admin = await admin_check(message)
        if not admin:
            return await message.answer("📛 Только администраторы могут использовать эту команду")

        await check_user_in_database(message)
        
        target_user = message.reply_to_message.from_user
        if not target_user:
            return await message.answer("❌ Пользователь не найден, ответьте на сообщение пользователя, которого хотите кикнуть.")

        await message.chat.ban(user_id=target_user.id)

        unban_kb = create_unban_kb(target_user.id)
        await message.answer(f"🐷 Пользователь @{target_user.username} был <b>забанен</b>!\n🚨 Больше ему тут не рады.", parse_mode='HTML', reply_markup=unban_kb)
        await message.reply_to_message.delete()
    except Exception as e:
        logger.error(f"Error in group_kick: {e}")

@group_router.callback_query(F.data.startswith('unban_user='))
async def group_unban_user(cb: types.CallbackQuery):
    try:
        user_id = int(cb.data.replace('unban_user=', ''))
        confirm = await admin_check(cb.message)
        if not confirm:
            return await cb.message.answer("📛 Только администраторы могут использовать эту команду")

        await cb.message.chat.unban(user_id=user_id)
        await cb.message.answer(f'✅ Пользователь {user_id} был разбанен.')
        await cb.answer(f'✅ Пользователь {user_id} был разбанен.')

    except Exception as e:
        logger.error(f'Error in group_unban_user: {e}')

@group_router.message(F.text == "+")
async def add_respect(message: types.Message):
    try:
        await check_user_in_database(message)
        server_id = str(message.chat.id).replace('-', '')
        pg = PostgresHandlerServer()

        target_id = message.reply_to_message.from_user
        user = pg.get_user(server_id, target_id.id)

        if user:
            last_respect = datetime.strptime(user.last_respect, '%Y-%m-%d %H:%M:%S')  # преобразуем строку в объект datetime
            if (datetime.now() - last_respect) > timedelta(minutes=15):  # сравниваем текущее время с последним временем выдачи репутации
                await message.answer(f"✅ Вы успешно добавили репутацию пользователю @{target_id.username} (+1)!\n🌈 Теперь у него {user.respect + 1} репутации.")
                pg.add_last_respect(server_id, target_id.id)
                pg.add_respect(server_id, target_id.id)
            else:
                await message.answer(f"❌ Вы уже добавили репутацию пользователю @{target_id.username} менее чем 15 минут назад!")
                return

    except Exception as e:
        logger.error(f"Error in add_respect: {e}")

@group_router.message(F.text == "-")
async def del_respect(message: types.Message):
    try:
        await check_user_in_database(message)
        server_id = str(message.chat.id).replace('-', '')
        pg = PostgresHandlerServer()

        target_id = message.reply_to_message.from_user
        user = pg.get_user(server_id, target_id.id)

        if user:
            last_respect = datetime.strptime(user.last_respect, '%Y-%m-%d %H:%M:%S')  # преобразуем строку в объект datetime
            if (datetime.now() - last_respect) > timedelta(minutes=15):  # сравниваем текущее время с последним временем выдачи репутации
                await message.answer(f"➖ Вы успешно убрали репутацию пользователю @{target_id.username} (-1)!\n🌈 Теперь у него {user.respect - 1} репутации.")
                pg.add_last_respect(server_id, target_id.id)
                pg.del_respect(server_id, target_id.id)
            else:
                await message.answer(f"❌ Вы уже забирали репутацию пользователю @{target_id.username} менее чем 15 минут назад!")
                return

    except Exception as e:
        logger.error(f"Error in del_respect: {e}")

@group_router.message(Command('ask'))
async def group_ask(message: types.Message, state: FSMContext):
    try:
        await check_user_in_database(message)

        await message.answer('🤔 Напишите вопрос:')
        await state.set_state(Ask.waiting_for_text)
    except Exception as e:
        logger.error(f"Error in group_ask: {e}")

@group_router.message(Ask.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    try:
        from g4f.client import Client

        client_groq = Client(
            api_key='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'
        )

        text = message.text
        await state.update_data(text=text)

        response = client_groq.chat.completions.create(
            model="",
            provider="Groq",
            messages=[
                {"role": "user", "content": text}
            ]
        )
        start_msg = await message.answer(f'🤖 Бот уже думает над вашим вопросом.. Прошу чуть подождать!\nЗапрос: {text}')
        response_text = response.choices[0].message.content
        chunk_size = 25  # размер чанка в символах

        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            await start_msg.edit_text(f'{start_msg.text}\nОтвет: {chunk}')
            await asyncio.sleep(0.2)  # задержка между чанками

        await state.clear()

    except Exception as e:
        logger.error(f"Error in process_text: {e}")
        await message.answer('Произошла ошибка при обработке вашего вопроса. Пожалуйста, повторите позже.')

@group_router.message(Command('8ball'))
async def group_8ball(message: types.Message):
    try:
        await check_user_in_database(message)
        text = message.text
        match = re.search(r'^(?:/8ball|8ball) (.+)$', text, re.IGNORECASE)
        if not match:
            return await message.answer("🥴 <b>Неверно введена команда</b>, пример:\n<code>/8ball Как ты думаешь, хомяк взлетит?</code>", parse_mode='HTML')
        
        ebr = EightBallReply()
        await message.reply(f"🎱 <b>{ebr.get_random_answer()}</b>", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in group_8ball: {e}")

@group_router.callback_query(NewUser.step_one)
@group_router.callback_query(F.data.startswith('approve_new_user='))
async def not_robot_user(cb: types.CallbackQuery, state: FSMContext):
    try:
        user_id = cb.from_user.id
        data = await state.get_data()
        message_id = data.get('message_id')

        await bot.restrict_chat_member(cb.message.chat.id, user_id, permissions=types.ChatPermissions(can_send_messages=True))
        await bot.edit_message_text(f"😎 Привет, @{cb.from_user.username}, добро пожаловать, теперь, ты можешь отправлять сообщения.", chat_id=cb.message.chat.id, message_id=message_id)
        await cb.answer()
        await state.clear()
    except Exception as e:
        logger.error(f"Error in not_robot_user: {e}")

@group_router.message(F.text == 'Настройки')
async def group_message_settings(message: types.Message):
    try:
        await group_settings(message)
    except Exception as e:
        logger.error(f"Error in group_message_settings: {e}")

@group_router.message(Command('settings'))
async def group_settings(message: types.Message):
    try:
        await check_user_in_database(message)
        group_settings_kb = create_settings_kb(message.chat.id)
        await message.answer('🛠 Внизу ты можешь настроить бота для вашего сервера.', reply_markup=group_settings_kb)
    except Exception as e:
        logger.error(f"Error in group_settings: {e}")

@group_router.callback_query(F.data.startswith('welcome_users='))
async def is_welcome_users(cb: types.CallbackQuery):
    try:
        admin = await admin_check(cb.message)
        if not admin:
            return cb.answer("📛 Только администраторы могут использовать эту команду, вам еще рано)")

        server_id = cb.data.replace('welcome_users=', '')
        server_id_pg = str(server_id.replace('-', ''))
        pg = PostgresHandlerServer()
        data = pg.get_server_settings(int(server_id_pg))
        welcome_users = data.welcome_users
        if welcome_users:
            welcome_users = False
        else:
            welcome_users = True

        pg.update_welcome_users(int(server_id_pg), welcome_users)

        await cb.message.answer(f"✅ Приветствее пользователей: {'Включено' if welcome_users else 'Выключено'}")
        await cb.answer()
    except Exception as e:
        logger.error(f"Error in welcome_users: {e}")

@group_router.callback_query(F.data.startswith('goodbye_users='))
async def is_goodbye_users(cb: types.CallbackQuery):
    try:
        admin = await admin_check(cb.message)
        if not admin:
            return cb.answer("📛 Только администраторы могут использовать эту команду, вам еще рано)")

        server_id = cb.data.replace('goodbye_users=', '')
        server_id_pg = str(server_id.replace('-', ''))
        pg = PostgresHandlerServer()
        data = pg.get_server_settings(int(server_id_pg))
        goodbye_users = data.goodbye_users
        if goodbye_users:
            goodbye_users = False
        else:
            goodbye_users = True

        pg.update_goodbye_users(int(server_id_pg), goodbye_users)

        await cb.message.answer(f"✅ Прощайте с пользователями: {'Включено' if goodbye_users else 'Выключено'}")
        await cb.answer()
    except Exception as e:
        logger.error(f"Error in goodbye_users: {e}")

@group_router.message(F.text == 'Пара')
async def group_text_couple(message: types.Message):
    try:
        await group_couple(message)
    except Exception as e:
        logger.error(f"Error in group_text_couple: {e}")

@group_router.message(Command('couple'))
async def group_couple(message: types.Message):
    try:
        await check_user_in_database(message)

        pg = PostgresHandlerServer()
        chat_id = str(message.chat.id).replace('-', '')
        usernames = pg.get_random_user_couple(int(chat_id))
        if len(usernames) == 2:
            await message.answer(f"👫 @{usernames[0]} и @{usernames[1]} -- пара дня ❤️‍🔥")
        else:
            await message.answer(f"😔 На данный момент нет пар в вашем чате.")
    except Exception as e:
        logger.error(f"Error in group_couple: {e}")

@group_router.message(Command('top_karma'))
async def group_top_karma(message: types.Message):
    try:
        pg = PostgresHandlerServer()
        chat_id = str(message.chat.id)

        chat_id = chat_id.replace('-', '')
        usernames = pg.get_top_karma(int(chat_id))
        if usernames is None:
            raise ValueError("Usernames are None")

        if len(usernames) == 0:
            text = "😔 На данный момент нет пользователей в вашем чате."
        else:
            usernames_str = "\n".join([f"👤 <b>@{username}</b> : <b>{respect}</b>" for username, respect in usernames])
            text = f"👑 Топ-5 пользователей в вашем чате по карме:\n\n{usernames_str}"

        await message.reply(text, parse_mode='HTML')
    except ValueError as e:
        logger.error(f"Error in top_karma: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
    except Exception as e:
        logger.error(f"Unexpected error in top_karma: {e}")
        await message.answer("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")

async def fetch_bitcoin_price():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), trust_env=True) as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return (await response.json())["bitcoin"]["usd"]
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f"Network error occurred: {e}")
        return None

@group_router.message(Command('bitcoin'))
async def group_bitcoin(message: types.Message):
    price = await fetch_bitcoin_price()
    
    if price is not None:
        await message.answer(
            f"💰 Курс биткоина: <b>{price}$</b> это примерно ~ <b>{price * 90} рублей</b>\n"
            f"📊 Данные обновляются каждые 5 минут.",
            parse_mode='HTML'
        )
    else:
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")

@group_router.message()
async def bad_words_respects(message: types.Message): #TODO иногда команды не работают, из-за этой проверки, пофиксить
    try:
        is_or_no = sch.predict([message.text])
        logger.info(f"Сообщение от пользователя {message.from_user.id} содержит ли нецензурные слова: {is_or_no}")

        if is_or_no == [0]:
            return
        
        if not message.text:
            return
        
        if message.text.startswith('/'):
            return

        pg = PostgresHandlerServer()
        server_id = str(message.chat.id).replace('-', '')
        await message.reply("😡 Сообщение содержит нецензурные слова!\n👨‍💻 Ваша карма уменьшена на -1!")
        logger.info(f"Удалено сообщение с нецензурным содержанием от пользователя {message.from_user.id}")
        pg.del_respect(int(server_id), message.from_user.id)
    except Exception as e:
        logger.error(f"Error in bad_words_respects: {e}")