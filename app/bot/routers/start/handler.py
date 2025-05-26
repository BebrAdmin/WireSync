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
from app.db import (
    get_user_by_tg_id,
    get_user_by_email,
    create_user,
    set_user_authenticated,
    get_invite_by_code,
    set_invite_used,
    add_user_server_access,
    get_servers_for_user,
    get_server_by_id,
    get_admin_api_data_for_server,
    create_server_api_data,
    get_server_api_data_by_server_id_and_user_id,
    get_server_api_data_by_server_id_and_tg_id,
)
from sqlalchemy import select, update
from app.db import AsyncSessionLocal, User
from app.bot.routers.main.keyboard import main_menu_keyboard
from app.bot.utils import generate_password, generate_api_token
from app.wireguard_api.users import create_user as wg_create_user, get_user_by_id, update_user_by_id

logger = logging.getLogger("user_register")

router = Router()
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

PROMPTS = {
    UserRegisterState.password: "Enter invite code to register:",
    UserRegisterState.email: "Enter your email:",
    UserRegisterState.phone: "Please send your phone number using the button below:",
    UserRegisterState.department: "Enter your department/position:",
}

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    user = await get_user_by_tg_id(message.from_user.id)
    if user and getattr(user, "is_registered", False):
        is_admin = bool(user and getattr(user, "is_admin", False))
        await message.answer(
            "👋 You are already registered.",
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
            "You need to complete registration to access the system.",
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
            "You need to complete registration to access the system.",
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
    invite_code = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()

    invite = await get_invite_by_code(invite_code)
    if not invite or not invite.is_active:
        await bot.edit_message_text(
            "❌ Invalid or inactive invite code. Please try again:",
            chat_id=message.chat.id,
            message_id=bot_message_id
        )
        return

    await set_invite_used(invite.id, message.from_user.id)
    await state.update_data(invite_code=invite_code)

    user = await get_user_by_tg_id(message.from_user.id)
    is_admin = bool(getattr(invite, "is_admin", False))

    if not user:
        user = await create_user({
            "tg_id": message.from_user.id,
            "tg_name": message.from_user.full_name,
            "is_authenticated": True,
            "is_admin": is_admin,
        })
        logger.info(f"User {message.from_user.id} ({message.from_user.full_name}) registered with invite code (is_admin={is_admin})")
    else:
        await set_user_authenticated(message.from_user.id, True, is_admin=is_admin)
        logger.info(f"User {message.from_user.id} ({message.from_user.full_name}) authenticated with invite code (is_admin={is_admin})")

    await state.clear()
    await bot.edit_message_text(
        "You need to complete registration to access the system.",
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=registration_entry_keyboard()
    )
    await state.update_data(bot_message_id=bot_message_id, invite_code=invite_code)

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
            "❌ Invalid email or already registered. Enter another email:",
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
            "❌ Enter your department/position:",
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=restart_keyboard()
        )
        return
    await state.update_data(department=department)
    data = await state.get_data()
    text = (
        f"Please check your data:\n"
        f"Email: {data['email']}\n"
        f"Phone: {data['phone']}\n"
        f"Department/Position: {data['department']}\n\n"
        f"Is everything correct?"
    )
    await state.set_state(UserRegisterState.waiting_confirm_action)
    await bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=confirm_keyboard()
    )

@router.callback_query(F.data == "confirm_register", UserRegisterState.waiting_confirm_action)
async def confirm_registration(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    await state.clear()
    await callback.answer("✅ Registration completed! Welcome!")
    await callback.message.delete()
    user = await get_user_by_tg_id(callback.from_user.id)
    is_admin = bool(user and getattr(user, "is_admin", False))
    await callback.message.answer(
        "Main Menu",
        reply_markup=main_menu_keyboard(is_admin=is_admin)
    )
    async with AsyncSessionLocal() as db_session:
        await db_session.execute(
            update(User)
            .where(User.tg_id == callback.from_user.id)
            .values(
                email=data["email"],
                phone=data["phone"],
                department=data["department"],
                is_registered=True,
            )
        )
        await db_session.commit()
    logger.info(
        f"User {callback.from_user.id} completed registration"
    )

    # --- WG PORTAL USER CREATION ---
    invite = await get_invite_by_code(data.get("invite_code"))
    if not invite:
        logger.error(f"Invite not found for user {user.id}")
        return

    admin_tg_id = getattr(invite, "admin_tg_id", None)
    if not admin_tg_id:
        logger.error(f"Invite {invite.code} does not have admin_tg_id set")
        return

    # Добавляем доступ к серверам только если сервер существует в БД (любой статус)
    for server_id in invite.server_ids:
        server = await get_server_by_id(server_id)
        if not server:
            logger.warning(f"Skip user_server_access for server_id={server_id}: not found")
            continue
        try:
            await add_user_server_access(user.id, server_id)
            logger.info(f"Granted access: user_id={user.id} to server_id={server_id}")
        except Exception as e:
            logger.error(f"Failed to grant access for user_id={user.id} to server_id={server_id}: {e}")

    password = generate_password()
    api_token = generate_api_token()
    errors = []

    for server_id in invite.server_ids:
        server = await get_server_by_id(server_id)
        if not server or getattr(server, "status", None) != "active":
            logger.warning(f"WG: skip server_id={server_id}: not found or not active")
            continue

        admin_api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, admin_tg_id)
        if not admin_api_data:
            logger.error(f"Cannot get admin API data for server_id={server_id}")
            errors.append(f"server_id={server_id}: no admin API data")
            continue

        # Проверка перед созданием server_api_data
        existing_api_data = await get_server_api_data_by_server_id_and_user_id(server_id, user.id)
        if existing_api_data:
            logger.info(f"Server API data already exists for user_id={user.id} on server_id={server_id}, skipping creation.")
            continue

        try:
            existing_user = await get_user_by_id(
                session=session,
                api_url=server.api_url,
                api_user=admin_api_data.api_login,
                api_pass=admin_api_data.api_password,
                user_id=str(user.tg_id)
            )
        except Exception as e:
            logger.warning(f"WG API not available or user not found on server_id={server_id}: {e}")
            existing_user = None

        payload = {
            "ApiToken": api_token,
            "Department": data["department"],
            "Disabled": False,
            "DisabledReason": "",
            "Email": data["email"],
            "Firstname": user.tg_name,
            "Identifier": str(user.tg_id),
            "IsAdmin": is_admin,
            "Lastname": "",
            "Locked": False,
            "LockedReason": "",
            "Notes": "",
            "Password": password,
            "Phone": data["phone"],
            "Source": "db"
        }
        success = False
        for attempt in range(3):
            try:
                if existing_user:
                    await update_user_by_id(
                        session=session,
                        api_url=server.api_url,
                        api_user=admin_api_data.api_login,
                        api_pass=admin_api_data.api_password,
                        user_id=str(user.tg_id),
                        user_data=payload
                    )
                    logger.info(f"WG portal user updated for user_id={user.id} on server_id={server_id}")
                else:
                    try:
                        await wg_create_user(
                            session=session,
                            api_url=server.api_url,
                            api_user=admin_api_data.api_login,
                            api_pass=admin_api_data.api_password,
                            user_data=payload
                        )
                        logger.info(f"WG portal user created for user_id={user.id} on server_id={server_id}")
                    except Exception as e:
                        # Если 409 - пользователь уже есть, делаем update
                        if "409" in str(e) or "already exists" in str(e):
                            await update_user_by_id(
                                session=session,
                                api_url=server.api_url,
                                api_user=admin_api_data.api_login,
                                api_pass=admin_api_data.api_password,
                                user_id=str(user.tg_id),
                                user_data=payload
                            )
                            logger.info(f"WG portal user updated after 409 for user_id={user.id} on server_id={server_id}")
                        else:
                            logger.error(f"WG API error on create for user_id={user.id} on server_id={server_id}: {e}")
                            break

                # Проверка перед созданием server_api_data (ещё раз, на всякий случай)
                existing_api_data = await get_server_api_data_by_server_id_and_user_id(server_id, user.id)
                if existing_api_data:
                    logger.info(f"Server API data already exists for user_id={user.id} on server_id={server_id}, skipping creation.")
                    success = True
                    break

                await create_server_api_data({
                    "server_id": server_id,
                    "user_id": user.id,
                    "api_login": str(user.tg_id),
                    "api_password": api_token,
                    "tg_id": user.tg_id
                })
                success = True
                break
            except Exception as e:
                logger.error(f"Failed to create/update WG portal user for user_id={user.id} on server_id={server_id} (attempt {attempt+1}/3): {e}")
        if not success:
            errors.append(f"server_id={server_id}: failed to create/update WG user after 3 attempts")

    if errors:
        logger.error(f"User {user.id} registration: some WG accounts were not created or updated: {errors}")

@router.callback_query(F.data == "edit_register")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    msg = await callback.message.edit_text(
        "You need to complete registration to access the system.",
        reply_markup=registration_entry_keyboard()
    )
    await state.update_data(bot_message_id=msg.message_id)