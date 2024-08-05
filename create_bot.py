import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import nltk
import ssl

from db_handler.db_handler import PostgresHandler

pg_db = PostgresHandler()
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
admins = [int(admin_id) for admin_id in config('ADMINS').split(',')]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    nltk.download('stopwords')
    scheduler.start() # запускает планировщик заданий. Это позволяет выполнять задачи по расписанию, например, каждый день в 10:00 он будет отправлять сообщение всем пользователям, зарегистрированным в базе данных, с уведомлением о том, что настала их регистрация.
    
    bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
except Exception as e:
    logger.error(f'Error in create_bot: {e}')
