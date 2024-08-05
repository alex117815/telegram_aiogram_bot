from aiogram.fsm.state import State, StatesGroup

class UserInfoForm(StatesGroup):
    waiting_for_user_id = State()
    message = State()
    user_id = State()

class SendMessForm(StatesGroup):
    waiting_for_text = State()
    text = State()
    waiting_for_image = State()
    message = State()
    choose = State()
    picture = State()
    spam = State()

class AddAdminForm(StatesGroup):
    waiting_for_user_id = State()
    message = State()
    user_id = State()

class DelAdminForm(StatesGroup):
    waiting_for_user_id = State()
    message = State()
    user_id = State()

class OnlineTicket(StatesGroup):
    admin_send_messages = State()
    wait = State()
    user_send_messages = State()

class SendMessageProfile(StatesGroup):
    wait = State()