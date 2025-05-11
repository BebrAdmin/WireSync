from aiogram.fsm.state import StatesGroup, State

class ServerRegisterState(StatesGroup):
    name = State()
    description = State()
    api_url = State()
    api_login = State()
    api_password = State()
    confirm = State()