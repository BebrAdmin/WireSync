from aiogram.fsm.state import StatesGroup, State

class AdapterCreateState(StatesGroup):
    waiting_confirm = State()
    custom_config = State()