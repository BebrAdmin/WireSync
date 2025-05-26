from aiogram.fsm.state import StatesGroup, State

class CreateInviteState(StatesGroup):
    select_admin = State()
    select_servers = State()
    confirm = State()