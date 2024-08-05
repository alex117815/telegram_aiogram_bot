class User:
    def __init__(self, id_, username, name, verified, date_reg, who_invited, referals, referal_link, admin, location, banned):
        """
        Инициализирует объект User с заданными параметрами.

        Args:
            id_ (int): Идентификатор пользователя.
            username (str): Имя пользователя.
            name (str): Имя пользователя.
            verified (bool): Верифицирован пользователь или нет.
            date_reg (str): Дата регистрации пользователя.
            who_invited (int): Идентификатор пользователя, пригласившего текущего пользователя.
            referals (int): Количество рефералов, совершенных пользователем.
            referal_link (str): Реферальная ссылка пользователя.
            admin (bool): Является ли пользователь администратором или нет.
            location (str): Местоположение пользователя.
            banned (bool): Является ли забанен пользователь или нет.
        """
        self.id : int = id_
        """Айди юзера."""

        self.username : str = username
        """Юзернейм."""

        self.name : str = name
        """Имя юзера."""

        self.verified : bool = verified
        """Верифицирован или нет (по номеру)."""

        self.date_reg : str = date_reg
        """Дата когда юзер зашел в бота."""

        self.who_invited : int = who_invited
        """Айди юзера кто пригласил, если таковой есть."""

        self.referals : int = referals
        """Кол-во приглашенных рефералов."""

        self.referal_link : str = referal_link
        """Реферальная ссылка."""

        self.admin : bool = admin
        """Админ или нет."""

        self.location : str = location
        """Локация, показывается только если юзер верифицирован."""

        self.banned : bool = banned
        """Забанен или нет."""

class Admins:
    def __init__(self, total_admins, id_, status, date_start):
        """
        Инициализирует объект Admins с заданными параметрами.

        Args:
            total_admins (int): Общее количество администраторов.
            id_ (int): Идентификатор администратора.
            status (str): Статус администратора.
            date_start (str): дата добавления администратора.
        """
        self.total_admins : int = total_admins
        """Общее кол-во админов."""

        self.id : int = id_
        """Айди админа."""

        self.status : str = status
        """Статус админа, например "helper"."""

        self.date_start : str = date_start
        """Дата, когда админ был добавлен."""

class Ticket:
    def __init__(self, total_tickets, ticket_id, ticket_text, ticket_photo, status, date_created, user_id, admin_id, views):
        """
        Инициализирует объект Ticket с заданными параметрами.

        Args:
            total_tickets (into): Общее количество билетов.
            ticket_id (int): Идентификатор билета.
            ticket_text (str): Текст билета.
            ticket_photo (str): Фотография билета.
            status (str): Статус билета.
            date_created (str): Дата создания билета.
            user_id (int): Идентификатор пользователя, связанного с тикетом.
            admin_id (int): идентификатор администратора, связанного с тикетом.
            views (int): Количество просмотров, которые имеет билет.
        """
        self.total_tickets : int = total_tickets
        """Общее количество билетов."""

        self.ticket_id : int = ticket_id
        """Идентификационный номер билета."""

        self.text : str = ticket_text
        """Текст билета."""

        self.photo : bool = ticket_photo
        """Фотография к билету."""

        self.status : str = status
        """Статус тикета."""

        self.date : str = date_created
        """Дата создания тикета."""

        self.user_id : int = user_id
        """Юзер айди."""

        self.admin_id : int = admin_id
        """Айди админа, который принял тикет."""

        self.views : int = views
        """Кол-во просмотров тикета."""
