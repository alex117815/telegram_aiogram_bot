import random

class EightBallReply():
    def __init__(self):
        """
        Инициализируйте экземпляр класса ответов "Восемь шаров".

        Этот класс представляет возможные ответы на вопрос "Волшебные 8 шаров".
        """
        # Позитивные ответы
        self.yes = 'Да.'
        self.yesyesyes = 'Да, да, да!!'

        # 50/50 ответы
        self.idk = 'Не знаю'
        self.maybe = 'Быть может' 
        self.totaly = 'Весьма вероятно'

        # Негативные ответы
        self.totaly_no = 'СОВЕРШЕННО НЕТ!'
        self.totaly_yes = 'СОВЕРШЕННО ДА!!!'

        # Не то не се ответы
        self.irejict = 'Я против этого, но возможно'
        self.idontsure = 'Я не могу ответить на этот вопрос'

        # Открытые ответы
        self.early = 'Рано..'
        self.forget = 'Забудь об этом'

        # Нейтральные ответы
        self.notbad = 'Не плохо'
        self.no = 'Нет'

    def get_random_answer(self):
        return random.choice([self.yes, self.yesyesyes, self.idk, self.maybe, self.totaly, self.totaly_no, self.totaly_yes, self.irejict, self.idontsure, self.early, self.forget, self.notbad, self.no])

class User:
    def __init__(self, server_id: int, user_id: int, username: str, admin: bool, date_start: str, respect: int, last_respect: str, messages: int):
        """
        Инициализирует объект User с указанными параметрами.

        Аргументы:
            server_id (int): Идентификатор сервера.
            user_id (int): Идентификатор пользователя.
            username (str): Имя пользователя.
            admin (bool): Указывает, является ли пользователь администратором или нет.
            date_start (str): Дата регистрации в формате "ГГГГ-ММ-ДД ЧЧ:ММ:СС".
            respect (int): количество раз, когда пользователь проявил уважение.
            last_respect (str): время последнего проявления уважения пользователем.
        """

        self.server_id : int = server_id
        """Сервер id, без "-" в начале."""

        self.user_id : int = user_id
        """Айди пользователя."""

        self.username : str = username
        """@username пользователя"."""

        self.admin : bool = admin
        """Админ юзер или нет."""

        self.date_start : str = date_start
        """Дата регестрации в формате "YYYY-MM-DD HH:MM:SS"."""

        self.respect : int = respect
        """Кол-во респектов (сколько раз ответили "+" или "-")."""

        self.last_respect : str = last_respect
        """Время когда сам юзер выдал или забрал респект."""

        self.messages : int = messages
        """Кол-во сообщений юзера."""

class ServerSettigns:
    def __init__(self, server_id: int, welcome_users: bool, goodbye_users: bool, total_users: int):
        """
        Инициализируйте объект настроек сервера с заданными параметрами.

        Args:
            server_id (int): Идентификатор сервера.
            welcome_users (bool): Следует ли приветствовать новых пользователей.
            total_users (into): общее количество пользователей на сервере.
        """

        self.server_id: int = server_id
        """Айди сервера"""

        self.welcome_users: bool = welcome_users
        """Првиетствовать новых юзеров, дефолт да"""

        self.goodbye_users = goodbye_users
        """Следует ли прощать юзеров, дефолт да"""

        self.total_users: int = total_users
        """Общее количество юзеров на сервере"""