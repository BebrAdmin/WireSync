import re
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from .keyboard import (
    registration_entry_keyboard,
    confirm_keyboard,
    phone_reply_keyboard,
    restart_keyboard,
)
from .fsm import UserRegisterState
from app.db import get_user_by_tg_id, get_user_by_email, create_user, set_user_authenticated
from sqlalchemy import select, update
from app.db import AsyncSessionLocal, User
from app.bot.routers.main.keyboard import main_menu_keyboard

logger = logging.getLogger("user_register")

router = Router()
REGISTRATION_PASSWORD = "Aa123456"
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

PROMPTS = {
    UserRegisterState.password: "Введите пароль для регистрации:",
    UserRegisterState.email: "Введите ваш email:",
    UserRegisterState.phone: "Пожалуйста, отправьте свой номер через кнопку ниже:",
    UserRegisterState.department: "Введите ваш отдел/должность:",
}

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    user = await get_user_by_tg_id(message.from_user.id)
    if user and getattr(user, "is_registered", False):
        is_admin = bool(user and getattr(user, "is_admin", False))
        await message.answer(
            "👋 Вы уже зарегистрированы.",
            reply_markup=main_menu_keyboard(is_admin=is_admin)
        )
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    is_first = not users

    if user and getattr(user, "is_authenticated", False):
        await state.clear()
        msg = await message.answer(
            "Для доступа необходимо пройти регистрацию.",
            reply_markup=registration_entry_keyboard()
        )
        await state.update_data(bot_message_id=msg.message_id)
        return

    if is_first:
        await create_user({
            "tg_id": message.from_user.id,
            "tg_name": message.from_user.full_name,
            "is_authenticated": True,
            "is_admin": True,
        })
        logger.info(f"First user {message.from_user.id} ({message.from_user.full_name}) created as admin")
        await state.clear()
        msg = await message.answer(
            "Для доступа необходимо пройти регистрацию.",
            reply_markup=registration_entry_keyboard()
        )
        await state.update_data(bot_message_id=msg.message_id)
        return

    await state.clear()
    msg = await message.answer(
        PROMPTS[UserRegisterState.password],
        reply_markup=None
    )
    await state.update_data(bot_message_id=msg.message_id)
    await state.set_state(UserRegisterState.password)

@router.message(UserRegisterState.password)
async def input_password(message: Message, state: FSMContext, bot):
    password = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()

    if password != REGISTRATION_PASSWORD:
        await bot.edit_message_text(
            "❌ Неверный пароль. Попробуйте снова:",
            chat_id=message.chat.id,
            message_id=bot_message_id
        )
        return

    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        await create_user({
            "tg_id": message.from_user.id,
            "tg_name": message.from_user.full_name,
            "is_authenticated": True,
            "is_admin": False,
        })
        logger.info(f"User {message.from_user.id} ({message.from_user.full_name}) passed authentication and was created")
    else:
        await set_user_authenticated(message.from_user.id, True, is_admin=False)
        logger.info(f"User {message.from_user.id} ({message.from_user.full_name}) passed authentication")

    await state.clear()
    await bot.edit_message_text(
        "Для доступа необходимо пройти регистрацию.",
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=registration_entry_keyboard()
    )
    await state.update_data(bot_message_id=bot_message_id)

@router.callback_query(F.data == "start_registration")
async def start_registration(callback: CallbackQuery, state: FSMContext):
    await state.update_data(bot_message_id=callback.message.message_id)
    await state.set_state(UserRegisterState.email)
    await callback.message.edit_text(
        PROMPTS[UserRegisterState.email],
        reply_markup=restart_keyboard()
    )

@router.message(UserRegisterState.email)
async def input_email(message: Message, state: FSMContext, bot):
    email = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    email_exists = await get_user_by_email(email)
    if not email or not re.match(EMAIL_REGEX, email) or email_exists:
        await bot.edit_message_text(
            "❌ Некорректный email или такой уже зарегистрирован. Введите другой email:",
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=restart_keyboard()
        )
        return
    await state.update_data(email=email)
    await state.set_state(UserRegisterState.phone)
    await bot.delete_message(chat_id=message.chat.id, message_id=bot_message_id)
    msg = await message.answer(
        PROMPTS[UserRegisterState.phone],
        reply_markup=phone_reply_keyboard()
    )
    await state.update_data(bot_message_id=msg.message_id)

@router.message(UserRegisterState.phone)
async def input_phone(message: Message, state: FSMContext, bot):
    if not message.contact or not message.contact.phone_number:
        await message.delete()
        return
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await state.set_state(UserRegisterState.department)
    await bot.delete_message(chat_id=message.chat.id, message_id=bot_message_id)
    msg = await message.answer(
        PROMPTS[UserRegisterState.department],
        reply_markup=restart_keyboard()
    )
    await state.update_data(bot_message_id=msg.message_id)

@router.message(UserRegisterState.department)
async def input_department(message: Message, state: FSMContext, bot):
    department = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    if not department:
        await bot.edit_message_text(
            "❌ Введите ваш отдел/должность:",
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=restart_keyboard()
        )
        return
    await state.update_data(department=department)
    data = await state.get_data()
    text = (
        f"Проверьте данные:\n"
        f"Email: {data['email']}\n"
        f"Телефон: {data['phone']}\n"
        f"Отдел/Должность: {data['department']}\n\n"
        f"Все верно?"
    )
    await state.set_state(UserRegisterState.waiting_confirm_action)
    await bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=confirm_keyboard()
    )

@router.callback_query(F.data == "confirm_register", UserRegisterState.waiting_confirm_action)
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await callback.answer("✅ Регистрация завершена! Добро пожаловать!")
    await callback.message.delete()
    user = await get_user_by_tg_id(callback.from_user.id)
    is_admin = bool(user and getattr(user, "is_admin", False))
    await callback.message.answer(
        "Main Menu",
        reply_markup=main_menu_keyboard(is_admin=is_admin)
    )
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.tg_id == callback.from_user.id)
            .values(
                email=data["email"],
                phone=data["phone"],
                department=data["department"],
                is_registered=True,
            )
        )
        await session.commit()
    logger.info(
        f"User {callback.from_user.id} completed registration: email={data['email']}, phone={data['phone']}, department={data['department']}"
    )

@router.callback_query(F.data == "edit_register")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    msg = await callback.message.edit_text(
        "Для доступа необходимо пройти регистрацию.",
        reply_markup=registration_entry_keyboard()
    )
    await state.update_data(bot_message_id=msg.message_id)