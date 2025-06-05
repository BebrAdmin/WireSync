from aiogram.fsm.state import StatesGroup, State

class CreateInviteState(StatesGroup):
    select_servers = State()