import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from .fsm import ServerRegisterState
from .keyboard import cancel_keyboard, confirm_keyboard
from app.db import (
    create_server, get_server_by_name, get_server_by_api_url,
    create_server_api_data, get_user_by_tg_id
)
from app.bot.routers.server_manager.handler import open_server_manager
from app.bot.routers.server_manager.keyboard import server_manager_keyboard
from app.wireguard_api.interfaces import get_all_interfaces

logger = logging.getLogger("server_register")

router = Router()

PROMPTS = {
    ServerRegisterState.name: "Введите имя сервера:",
    ServerRegisterState.description: "Введите описание сервера (или напишите -):",
    ServerRegisterState.api_url: "Введите API URL сервера:",
    ServerRegisterState.api_login: "Введите API login:",
    ServerRegisterState.api_password: "Введите API password (32-64 символа):",
}

NEXT_STATE = {
    ServerRegisterState.name: ServerRegisterState.description,
    ServerRegisterState.description: ServerRegisterState.api_url,
    ServerRegisterState.api_url: ServerRegisterState.api_login,
    ServerRegisterState.api_login: ServerRegisterState.api_password,
}

@router.callback_query(F.data == "register_server")
async def start_register_server(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ServerRegisterState.name)
    msg = await callback.message.edit_text(
        PROMPTS[ServerRegisterState.name],
        reply_markup=cancel_keyboard()
    )
    await state.update_data(bot_message_id=msg.message_id)

@router.message(StateFilter(ServerRegisterState.name))
async def input_server_name(message: Message, state: FSMContext, bot):
    name = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    if await get_server_by_name(name):
        await bot.edit_message_text(
            "Сервер с таким именем уже существует. Введите другое имя:",
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=cancel_keyboard()
        )
        return
    await state.update_data(name=name)
    await state.set_state(ServerRegisterState.description)
    await bot.edit_message_text(
        PROMPTS[ServerRegisterState.description],
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=cancel_keyboard()
    )

@router.message(StateFilter(ServerRegisterState.description))
async def input_server_description(message: Message, state: FSMContext, bot):
    desc = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    if desc == "-":
        desc = None
    await state.update_data(description=desc)
    await state.set_state(ServerRegisterState.api_url)
    await bot.edit_message_text(
        PROMPTS[ServerRegisterState.api_url],
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=cancel_keyboard()
    )

@router.message(StateFilter(ServerRegisterState.api_url))
async def input_api_url(message: Message, state: FSMContext, bot):
    url = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    if not (url.startswith("http://") or url.startswith("https://")):
        await bot.edit_message_text(
            "Некорректный URL. Введите корректный API URL сервера:",
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=cancel_keyboard()
        )
        return
    if await get_server_by_api_url(url):
        await bot.edit_message_text(
            "Сервер с таким API URL уже существует. Введите другой URL:",
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=cancel_keyboard()
        )
        return
    await state.update_data(api_url=url)
    await state.set_state(ServerRegisterState.api_login)
    await bot.edit_message_text(
        PROMPTS[ServerRegisterState.api_login],
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=cancel_keyboard()
    )

@router.message(StateFilter(ServerRegisterState.api_login))
async def input_api_login(message: Message, state: FSMContext, bot):
    api_login = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    if not api_login:
        await bot.edit_message_text(
            "API login не может быть пустым. Введите API login:",
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=cancel_keyboard()
        )
        return
    await state.update_data(api_login=api_login)
    await state.set_state(ServerRegisterState.api_password)
    await bot.edit_message_text(
        PROMPTS[ServerRegisterState.api_password],
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=cancel_keyboard()
    )

@router.message(StateFilter(ServerRegisterState.api_password))
async def input_api_password(message: Message, state: FSMContext, bot):
    api_password = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    if not (32 <= len(api_password) <= 64):
        await bot.edit_message_text(
            "Пароль должен быть от 32 до 64 символов. Попробуйте снова:",
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=cancel_keyboard()
        )
        return
    await state.update_data(api_password=api_password)
    data = await state.get_data()
    text = (
        f"Проверьте данные:\n"
        f"Имя: {data['name']}\n"
        f"Описание: {data['description'] or '—'}\n"
        f"API URL: {data['api_url']}\n"
        f"API login: {data['api_login']}\n"
        f"API password: {'*' * len(data['api_password'])}\n\n"
        f"Синхронизировать сервер?"
    )
    await state.set_state(ServerRegisterState.confirm)
    await bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=confirm_keyboard()
    )

@router.callback_query(F.data == "sync_server", StateFilter(ServerRegisterState.confirm))
async def sync_server(callback: CallbackQuery, state: FSMContext, bot, session, **kwargs):
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    try:
        await get_all_interfaces(
            session=session,
            api_url=data["api_url"],
            api_user=data["api_login"],
            api_pass=data["api_password"]
        )
    except Exception as e:
        err_text = str(e)
        if "401" in err_text:
            await callback.answer("❌ Неверные данные API. Проверьте логин и пароль.", show_alert=True)
        elif "500" in err_text:
            await callback.answer("❌ Ошибка синхронизации сервера.", show_alert=True)
        else:
            await callback.answer("❌ Не удалось подключиться к API.", show_alert=True)
        text = (
            f"Проверьте данные:\n"
            f"Имя: {data['name']}\n"
            f"Описание: {data['description'] or '—'}\n"
            f"API URL: {data['api_url']}\n"
            f"API login: {data['api_login']}\n"
            f"API password: {'*' * len(data['api_password'])}\n\n"
            f"Синхронизировать сервер?"
        )
        if callback.message.text != text:
            await bot.edit_message_text(
                text,
                chat_id=callback.message.chat.id,
                message_id=bot_message_id,
                reply_markup=confirm_keyboard()
            )
        else:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=bot_message_id,
                reply_markup=confirm_keyboard()
            )
        return

    server = await create_server({
        "name": data["name"],
        "description": data["description"],
        "api_url": data["api_url"],
        "status": "active"
    })
    # Получаем user_id администратора (создателя сервера)
    admin_user = await get_user_by_tg_id(callback.from_user.id)
    await create_server_api_data({
        "server_id": server.id,
        "user_id": admin_user.id,  # <-- обязательно!
        "api_login": data["api_login"],
        "api_password": data["api_password"],
        "tg_id": callback.from_user.id
    })
    logger.info(f"Server '{server.name}' was registered by user {callback.from_user.id}")
    await state.clear()
    await callback.answer("✅ Сервер синхронизирован!")
    await open_server_manager(callback, session)

@router.callback_query(F.data.in_(["to_server_manager", "decline_register", "cancel_register"]))
async def to_server_manager(callback: CallbackQuery, state: FSMContext, session):
    await state.clear()
    await callback.answer("Действие отменено.")
    await open_server_manager(callback, session)

@router.callback_query(F.data == "restart_register", StateFilter(ServerRegisterState.confirm))
async def restart_register(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await start_register_server(callback, state)