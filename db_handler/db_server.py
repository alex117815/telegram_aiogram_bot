# database_handler.py
import sqlite3
from sqlite3 import Error
from datetime import datetime
import logging
from typing import Optional
from cachetools import TTLCache, cached
from enums.group_enum import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgresHandlerServer:
    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.create_connection()

    user_cache = TTLCache(maxsize=32, ttl=360)
    """Кеш для юзеров, чтобы быстрее работало в мультипроцессе"""
    user_ids_cache = TTLCache(maxsize=32, ttl=360)
    """Кеш со всеми id юзеров. Для оптимизации запросов к базе"""
    server_settings_cache = TTLCache(maxsize=32, ttl=360)
    """Кеш с настройками сервера server_settings_"""
    top_karma_cache = TTLCache(maxsize=32, ttl=360)
    """Кеш для топ кармы"""

    def create_connection(self):
        try:
            self.conn = sqlite3.connect('servers.db', timeout=5)
            self.cursor = self.conn.cursor()
        except Error as e:
            logger.error(f"Error in create_connection: {e}")

    def create_table(self, server_id: int):
        if server_id is None:
            raise ValueError("server_id cannot be None")

        try:
            create_table_query = """
                CREATE TABLE IF NOT EXISTS server_temp (
                    server_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    username TEXT,
                    admin BOOLEAN,
                    date_start DATE DEFAULT CURRENT_TIMESTAMP,
                    respect INTEGER DEFAULT 0,
                    last_respect DATE DEFAULT CURRENT_TIMESTAMP,
                    messages INTEGER DEFAULT 0
                )
            """
            self.cursor.execute(create_table_query)

            create_table_settings_query = """
                CREATE TABLE IF NOT EXISTS server_temp_settings (
                    server_id INTEGER PRIMARY KEY,
                    welcome_users BOOLEAN DEFAULT TRUE,
                    goodbye_users BOOLEAN DEFAULT TRUE,
                    total_users INTEGER DEFAULT 0
                )
            """
            self.cursor.execute(create_table_settings_query)

            rename_table_query = f"ALTER TABLE server_temp RENAME TO server_{server_id};"
            self.cursor.execute(rename_table_query)

            rename_table_settings_query = f"ALTER TABLE server_temp_settings RENAME TO server_settings_{server_id};"
            self.cursor.execute(rename_table_settings_query)

            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error in create_table for server_{server_id}: {e}")

    def add_user(self, server_id: int, user_id: int, username: str, admin: Optional[bool] = False) -> None:
        if self.conn is None or self.cursor is None:
            raise ValueError("Database connection or cursor is None")

        try:
            date_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                f"INSERT INTO server_{server_id} (user_id, username, admin, date_start, respect, last_respect) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, admin, date_start, 0, date_start))
            self.conn.commit()
        except sqlite3.Error as e:
            if 'no such table' in str(e):
                self.create_table(server_id)
                self.add_user(server_id, user_id, username, admin)
            else:
                logger.error(f"Error in add_user for server_{server_id}, user_id {user_id}: {e}")

    def update_total_users(self, server_id: int, total_users: int):
        try:
            self.cursor.execute(f"INSERT OR REPLACE INTO server_settings_{server_id} (server_id, total_users) VALUES (?, ?)", (server_id, total_users))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in update_total_users for server_{server_id}: {e}")
    
    @cached(cache=user_cache)
    def get_user(self, server_id: int, user_id: int) -> Optional['User']:
        try:
            self.cursor.execute(f"SELECT * FROM server_{server_id} WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            if result:
                return User(*result)
        except Error as e:
            if 'no such table' in str(e):
                self.create_table(server_id)
                return self.get_user(server_id, user_id)
            else:
                logger.error(f"Error in get_user for server_{server_id}, user_id {user_id}: {e}")
                return None
        
    @cached(cache=user_ids_cache)
    def get_user_ids(self, server_id: int) -> list:
        """Получает список id юзеров с определенного сервера"""
        try:
            self.cursor.execute(f"SELECT user_id FROM server_{server_id}")
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error in get_user_ids for server_{server_id}: {e}")
            return []
        
    def add_respect(self, server_id: int, user_id: int):
        try:
            self.cursor.execute(f"UPDATE server_{server_id} SET respect = respect + 1 WHERE user_id = ?", (user_id,))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in add_respect for server_{server_id}, user_id {user_id}: {e}")

    def add_last_respect(self, server_id: int, user_id: int):
        try:
            self.cursor.execute(f"UPDATE server_{server_id} SET last_respect = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in add_last_respect for server_{server_id}, user_id {user_id}: {e}")

    def del_respect(self, server_id: int, user_id: int):
        try:    
            self.cursor.execute(f"UPDATE server_{server_id} SET respect = respect - 1 WHERE user_id = ?", (user_id,))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in del_respect for server_{server_id}, user_id {user_id}: {e}")

    def update_welcome_users(self, server_id: int, welcome_users: bool):
        try:
            self.cursor.execute(f"UPDATE server_settings_{server_id} SET welcome_users = ?", (welcome_users,))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in update_welcome_users for server_{server_id}: {e}")

    def update_goodbye_users(self, server_id: int, goodbye_users: bool):
        try:
            self.cursor.execute(f"UPDATE server_settings_{server_id} SET goodbye_users = ?", (goodbye_users,))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in update_goodbye_users for server_{server_id}: {e}")

    @cached(cache=server_settings_cache)
    def get_server_settings(self, server_id: int) -> dict:
        try:
            self.cursor.execute(f"SELECT * FROM server_settings_{server_id}")
            result = self.cursor.fetchone()
            if result:
                return ServerSettigns(*result)
        except Error as e:
            logger.error(f"Error in get_server_settings for server_{server_id}: {e}")
            return {}
        
    def get_all_servers(self) -> int:
        try:
            self.cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name LIKE 'server_settings_%'
            """)
            tables = self.cursor.fetchall()
            return len(tables)
        except Error as e:
            logger.error(f"Error in get_all_servers: {e}")
            return 0

    def get_total_users(self) -> int:
        try:
            self.cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name LIKE 'server_settings_%'
            """)
            tables = [row[0] for row in self.cursor.fetchall()]
            total_users = 0
            for table in tables:
                self.cursor.execute(f"SELECT total_users FROM {table}")
                total_users += sum(row[0] for row in self.cursor.fetchall())
            return total_users
        except Error as e:
            logger.error(f"Error in get_total_users: {e}")
            return 0

    def get_all_servers_ids(self) -> list:
        try:
            self.cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name LIKE 'server_settings_%'
            """)
            tables = [row[0] for row in self.cursor.fetchall()]
            server_ids = [table.split('_')[-1] for table in tables]
            return server_ids
        except Error as e:
            logger.error(f"Error in get_all_servers_ids: {e}")
            return []
        
    def get_random_user_couple(self, server_id: int) -> list:
        try:
            self.cursor.execute(f"SELECT username FROM server_{server_id} ORDER BY RANDOM() LIMIT 2")
            return [row[0] for row in self.cursor.fetchall()]
        except Error as e:
            logger.error(f"Error in get_random_user for server_{server_id}: {e}")
            return []
        
    @cached(cache=top_karma_cache)
    def get_top_karma(self, server_id: int) -> list:
        try:
            self.cursor.execute(f"SELECT username, respect FROM server_{server_id} ORDER BY respect DESC LIMIT 5")
            return [(row[0], row[1]) for row in self.cursor.fetchall()]
        except Error as e:
            logger.error(f"Error in get_top_karma for server_{server_id}: {e}")
            return []
        
    def check_chat_id(self, server_id: int) -> bool:
        try:
            self.cursor.execute(f"SELECT server_id FROM server_{server_id} WHERE server_id = ?", (server_id,))
            result = self.cursor.fetchone()
            if result:
                return True
        except Error as e:
            logger.error(f"Error in check_chat_id for server_{server_id}: {e}")
        return False
    
    def del_user(self, server_id: int, user_id: int):
        try:
            self.cursor.execute(f"DELETE FROM server_{server_id} WHERE user_id = ?", (user_id,))
            self.conn.commit()
        except Error as e:
            logger.error(f"Error in del_user for server_{server_id}: {e}")