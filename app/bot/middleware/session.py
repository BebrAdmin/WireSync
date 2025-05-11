from aiogram import BaseMiddleware

class SessionMiddleware(BaseMiddleware):
    def __init__(self, session):
        super().__init__()
        self.session = session

    async def __call__(self, handler, event, data):
        data["session"] = self.session
        return await handler(event, data)