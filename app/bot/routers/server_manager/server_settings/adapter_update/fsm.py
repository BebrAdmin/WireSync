from aiogram.fsm.state import StatesGroup, State

class AdapterUpdateState(StatesGroup):
    custom_config = State()