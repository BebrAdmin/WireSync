from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject
from app.db import get_user_by_tg_id

class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject = None, user_id: int = None) -> bool:
        tg_id = user_id or (event.from_user.id if event and event.from_user else None)
        if not tg_id:
            return False
        user = await get_user_by_tg_id(tg_id)
        return bool(user and getattr(user, "is_admin", False))