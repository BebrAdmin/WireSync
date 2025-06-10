from aiogram.fsm.state import StatesGroup, State

class UserRegisterState(StatesGroup):
    password = State()
    email = State()
    phone = State()
    department = State()
    waiting_confirm_action = State()