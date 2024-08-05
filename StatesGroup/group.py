from aiogram.fsm.state import State, StatesGroup

class Settings(StatesGroup):
    first_setup = State()

class Ask(StatesGroup):
    waiting_for_text = State()

class NewUser(StatesGroup):
    step_one = State()

class CrocodileGame(StatesGroup):
    waiting_for_users = State()