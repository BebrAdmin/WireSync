from aiogram.fsm.state import StatesGroup, State

class ServerRegisterState(StatesGroup):
    custom_config = State()
    select_users = State()