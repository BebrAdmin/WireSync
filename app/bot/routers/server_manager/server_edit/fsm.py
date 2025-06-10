from aiogram.fsm.state import StatesGroup, State

class ServerEditState(StatesGroup):
    custom_config = State()