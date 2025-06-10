from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

class MessageCleanerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            if not event.from_user or event.from_user.is_bot:
                return await handler(event, data)
            state: FSMContext = data.get("state")
            current_state = await state.get_state() if state else None
            if not current_state:
                if not (event.text and event.text.startswith('/')):
                    await event.delete()
                    return
        return await handler(event, data)