from aiogram import Router
from aiogram.types import Message

cleanup_router = Router()

@cleanup_router.message()
async def empty_handler(message: Message):
    pass