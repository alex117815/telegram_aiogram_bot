import asyncio
from create_bot import bot, dp
import logging

logger = logging.getLogger(__name__)

from handlers.start import main_router
from keyboard_handlers.admin import adm_keyboard
from keyboard_handlers.user import usr_keyboard
from keyboard_handlers.groups_kb import group_router

async def main():
    try:
        dp.include_router(adm_keyboard) #для админа
        dp.include_router(usr_keyboard) #для юзера
        dp.include_router(main_router) #главный
        dp.include_router(group_router)

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(e)

if __name__ == "__main__":
    asyncio.run(main())