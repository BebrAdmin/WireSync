from aiogram.fsm.state import StatesGroup, State

class DeleteUserState(StatesGroup):
    select_user = State()
    confirm = State()