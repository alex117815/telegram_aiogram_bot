from aiogram.fsm.state import State, StatesGroup

class WriteTicket(StatesGroup):
    waiting_for_text = State()
    picture = State()

class OnlineTicketUsr(StatesGroup):
    user_send_messages = State()
    wait = State()