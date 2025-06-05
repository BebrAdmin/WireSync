from aiogram.types import BotCommand

def get_bot_commands() -> list[BotCommand]:
    return [
        BotCommand(command="start", description="Запустить бота"),
    ]