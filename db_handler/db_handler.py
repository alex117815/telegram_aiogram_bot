#База данных
import sqlite3
from sqlite3 import Error
from datetime import datetime
import logging
import random
from cachetools import TTLCache, cached
from enums.db_handler_enum import *
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgresHandler:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.create_connection()
        self.create_table()

    def create_connection(self):
        self.conn = sqlite3.connect('database.db', timeout=5, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('PRAGMA journal_mode=WAL')
        self.cursor.execute('PRAGMA synchronous=NORMAL')

    def create_table(self) -> None:
        """
        Создает таблицы пользователей, администраторов и заявок, если они еще не существуют.
        """
        try:
            if self.cursor is None or self.conn is None:
                raise ValueError("Database connection or cursor is None")

            create_users_table_query = """CREATE TABLE IF NOT EXISTS users
                   (id INTEGER PRIMARY KEY,
                    username TEXT,
                    name TEXT,
                    verified BOOLEAN,
                    date_registration DATE,
                    who_invited INTEGER DEFAULT 0,
                    referals INTEGER DEFAULT 0,
                    referal_link TEXT,
                    admin BOOLEAN,
                    location TEXT,
                    banned BOOLEAN
                    )"""
            self.cursor.execute(create_users_table_query)

            create_admins_table_query = """CREATE TABLE IF NOT EXISTS admins
                   (total_admins INTEGER DEFAULT 0,
                    id INTEGER PRIMARY KEY,
                    status TEXT DEFAULT 'helper',
                    date_start DATE
                    )"""
            self.cursor.execute(create_admins_table_query)

            create_tickets_table_query = """
                CREATE TABLE IF NOT EXISTS tickets (
                total_tickets INTEGER DEFAULT 0,
                ticket_id INTEGER,
                ticket_text TEXT,
                ticket_photo TEXT,
                status TEXT,
                date_created DATE,
                user_id INTEGER,
                admin_id INTEGER,
                views INTEGER DEFAULT 0
                )"""
            self.cursor.execute(create_tickets_table_query)

            self.conn.commit()
        except Error as e:
            logger.error(f"Error in create_table: {e}")
        except AttributeError as e:
            logger.error(f"Error in create_table: {e}. Connection or cursor is None.")

    def add_user(self, user_id: int, username: str, name: str, who_invited: Optional[int] = None,
                 admin: Optional[bool] = None) -> None:
        try:
            admin = admin if admin is not None else False

            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (user_id, username, name, False, datetime.now(), who_invited or 0, 0, None, admin, None, False))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in add_user: {e}")

    def set_location(self, user_id, location):
        try:
            self.cursor.execute("UPDATE users SET location = ? WHERE id = ?", (location, user_id))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in set_location: {e}")

    referal_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=referal_cache)
    def get_referal_link(self, user_id):
        try:
            self.cursor.execute("SELECT referal_link FROM users WHERE id = ?", (user_id,)).fetchone()
        except Error as e:
            logger.error(f"Error in get_referal_link: {e}")

    def set_referal_link(self, user_id, referal_link):
        try:
            self.cursor.execute("UPDATE users SET referal_link = ? WHERE id = ?", (referal_link, user_id))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in set_referal_link: {e}")

    def update_referals(self, who_invited_id, referal_id):
        if self.conn is None or self.cursor is None:
            raise ValueError("Database connection or cursor is None")

        if who_invited_id is None or referal_id is None:
            raise ValueError("Argument can't be None")

        try:
            self.cursor.execute("UPDATE users SET who_invited = ?, referals = referals + 1 WHERE id = ?",
                               (referal_id, who_invited_id))
            self.conn.commit()
            logger.info(f"Обновлено!\nТеперь у {who_invited_id} новый реф: {referal_id}")
        except Error as e:
            logger.error(f"Error in update_referals: {e}")
            raise e

    def set_verified(self, user_id):
        try:
            self.cursor.execute("UPDATE users SET verified = ? WHERE id = ?", (True, user_id))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in set_verified: {e}")

    user_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=user_cache)
    def get_user(self, user_id):
        try:
            self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            if result:
                return User(*result)
        except Error as e:
            logger.error(f"Error in get_user: {e}")
        return None

    admin_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=admin_cache)
    def get_admin(self, user_id):
        try:
            self.cursor.execute("SELECT * FROM admins WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            if result:
                return Admins(*result)
        except Error as e:
            logger.error(f"Error in get_admin: {e}")
        return None

    all_users_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=all_users_cache)
    def get_all_users(self):
        try:
            self.cursor.execute("SELECT * FROM users")
            result = self.cursor.fetchall()
            if result:
                return [User(*user) for user in result]
        except Error as e:
            logger.error(f"Error in get_all_users: {e}")
        return None
    
    popular_locations_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=popular_locations_cache)
    def get_populars_locations(self):
        try:
            self.cursor.execute("SELECT location FROM users")
            result = self.cursor.fetchall()
            if result:
                return [result[0] for result in result]
        except Error as e:
            logger.error(f"Error in get_populars_locations: {e}")
        return None

    def update_admin(self, user_id, admin):
        try:
            status = 'helper'
            ids = self.get_all_ids()
            if user_id in ids:
                status = 'Owner'

            self.cursor.execute("UPDATE users SET admin = ? WHERE id = ?", (admin, user_id))
            self.cursor.execute("INSERT INTO admins VALUES (?, ?, ?, ?)", (0, user_id, status, datetime.now()))
            self.conn.commit()
            logger.info(f"Обновлено!, {user_id} - {admin}")
        except Error as e:
            logger.error(f"Error in update_admin: {e}")

    all_admins_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=all_admins_cache)
    def get_all_admins(self):
        try:
            self.cursor.execute("SELECT * FROM admins")
            result = self.cursor.fetchall()
            if result:
                return [Admins(*user) for user in result]
        except Error as e:
            logger.error(f"Error in get_all_admins: {e}")
        return None

    all_ids_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=all_ids_cache)
    def get_all_ids(self):
        try:
            self.cursor.execute("SELECT id FROM users")
            result = self.cursor.fetchall()
            if result:
                return [user[0] for user in result]
        except Error as e:
            logger.error(f"Error in get_all_ids: {e}")
        return None

    def add_admin(self, user_id):
        try:
            self.cursor.execute("INSERT OR IGNORE INTO admins VALUES (?, ?, ?, ?)", (0, user_id, 'helper', datetime.now()))
            self.cursor.execute("UPDATE OR IGNORE users SET admin = ? WHERE id = ?", (True, user_id))
            self.conn.commit()
        except Error as e:
            if 'UNIQUE constraint failed' in str(e):
                logger.info(f'Юзер {user_id} уже админ.')
            else:
                logger.error(f"Error in add_admin: {e}")

    def delete_admin(self, user_id):
        try:
            self.cursor.execute("DELETE FROM admins WHERE id = ?", (user_id))
            self.cursor.execute("UPDATE users SET admin = ? WHERE id = ?", (False, user_id))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in delete_admin: {e}")

    def new_ticket(self, user_id, ticket_text, ticket_photo=None):
        try:
            tickets = self.get_all_tickets()
            random_ticket_id = random.randint(1, 99990)
            self.cursor.execute("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (tickets, random_ticket_id, ticket_text, ticket_photo, 'Waiting', datetime.now(), user_id, 0, 0))
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error in new_ticket: {e}")

    all_tickets_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=all_tickets_cache)
    def get_all_tickets(self):
        try:
            self.cursor.execute("SELECT * FROM tickets")
            result = self.cursor.fetchall()
            if result:
                return [Ticket(*ticket) for ticket in result]
        except Error as e:
            logger.error(f"Error in get_all_tickets: {e}")
        return None

    tickets_cache = TTLCache(maxsize=32, ttl=660)
    @cached(cache=tickets_cache)
    def get_ticket(self, ticket_id):
        try:
            self.cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
            result = self.cursor.fetchone()
            if result:
                return Ticket(*result)
        except sqlite3.Error as e:
            logger.error(f"Error in get_ticket: {e}")
        return None
    
    def del_ticket(self, ticket_id):
        try:
            self.cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in del_ticket: {e}")

    def add_view(self, ticket_id):
        try:
            self.cursor.execute("UPDATE tickets SET views = views + 1 WHERE ticket_id = ?", (ticket_id,))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in add_view: {e}")

    def edit_ticket_status_and_admin_id(self, ticket_id, status, admin_id):
        try:
            self.cursor.execute("UPDATE tickets SET status = ?, admin_id = ? WHERE ticket_id = ?", (status, admin_id, ticket_id))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in edit_ticket_status_and_admin_id: {e}")
    
    def search_ticket_by_admin_info(self, admin_id):
        try:
            self.cursor.execute("SELECT * FROM tickets WHERE admin_id = ?", (admin_id,))
            result = self.cursor.fetchall()
            if result:
                return [Ticket(*ticket) for ticket in result]
        except Error as e:
            logger.error(f"Error in search_ticket_by_admin_info: {e}")
        return None
    
    def search_ticket_by_user_id(self, user_id):
        try:
            self.cursor.execute("SELECT * FROM tickets WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchall()
            if result:
                return [Ticket(*ticket) for ticket in result]
        except Error as e:
            logger.error(f"Error in search_ticket_by_user_id: {e}")
        return None
    
    def ban_profile(self, user_id):
        try:
            self.cursor.execute("UPDATE users SET banned = ? WHERE id = ?", (True, user_id))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in ban_profile: {e}")

    def unban_profile(self, user_id):
        try:
            self.cursor.execute("UPDATE users SET banned = ? WHERE id = ?", (False, user_id))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in unban_profile: {e}")