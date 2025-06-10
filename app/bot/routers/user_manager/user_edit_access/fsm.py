from aiogram.fsm.state import StatesGroup, State

class EditAccessState(StatesGroup):
    select_user = State()
    select_rights = State()
    confirm = State()