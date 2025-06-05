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
from app.bot.tasks.user_sync import sync_all_users_on_servers

logger = logging.getLogger("user_register")

router = Router()
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

PROMPTS = {
    UserRegisterState.password: "<b>Invite Code</b>\nEnter invite code to register:",
    UserRegisterState.email: "<b>Registration: Email</b>\nPlease enter your email address:",
    UserRegisterState.phone: "<b>Registration: Phone</b>\nPlease send your phone number using the button below:",
    UserRegisterState.department: "<b>Registration: Department/Position</b>\nEnter your department/position:",
}

def format_error_block(msg: str) -> str:
    return f"<blockquote>⚠️ {msg}</blockquote>\n"

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    user = await get_user_by_tg_id(message.from_user.id)
    if user and getattr(user, "is_registered", False):
        is_admin = bool(user and getattr(user, "is_admin", False))
        await message.answer(
            "Main Menu",
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
            "<b>Registration:</b>\nYou need to complete registration to access the system",
            reply_markup=registration_entry_keyboard(),
            parse_mode="HTML"
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
            "<b>Registration:</b>\nYou need to complete registration to access the system",
            reply_markup=registration_entry_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        return

    await state.clear()
    msg = await message.answer(
        "<b>Invite Code</b>\nEnter invite code to register:",
        reply_markup=None,
        parse_mode="HTML"
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
    error_text = ""
    if not invite or not invite.is_active:
        error_text = format_error_block("Invalid or inactive invite code. Please try again.")
        full_text = error_text + PROMPTS[UserRegisterState.password]
        last_error = data.get("last_error_text")
        if last_error == full_text:
            return
        await bot.edit_message_text(
            full_text,
            chat_id=message.chat.id,
            message_id=bot_message_id,
            parse_mode="HTML"
        )
        await state.update_data(last_error_text=full_text)
        return

    await set_invite_used(invite.id, message.from_user.id)
    await state.update_data(invite_code=invite_code, last_error_text=None)

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
        "<b>Registration:</b>\nYou need to complete registration to access the system",
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=registration_entry_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(bot_message_id=bot_message_id, invite_code=invite_code)

@router.callback_query(F.data == "start_registration")
async def start_registration(callback: CallbackQuery, state: FSMContext):
    await state.update_data(bot_message_id=callback.message.message_id, last_error_text=None)
    await state.set_state(UserRegisterState.email)
    await callback.message.edit_text(
        PROMPTS[UserRegisterState.email],
        reply_markup=restart_keyboard(),
        parse_mode="HTML"
    )

@router.message(UserRegisterState.email)
async def input_email(message: Message, state: FSMContext, bot):
    email = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    email_exists = await get_user_by_email(email)
    error_text = ""
    if not email or not re.match(EMAIL_REGEX, email) or email_exists:
        error_text = format_error_block("Invalid email or already registered. Please try again.")
        full_text = error_text + PROMPTS[UserRegisterState.email]
        last_error = data.get("last_error_text")
        if last_error == full_text:
            return
        await bot.edit_message_text(
            full_text,
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=restart_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(last_error_text=full_text)
        return
    await state.update_data(email=email, last_error_text=None)
    await state.set_state(UserRegisterState.phone)
    await bot.delete_message(chat_id=message.chat.id, message_id=bot_message_id)
    msg = await message.answer(
        PROMPTS[UserRegisterState.phone],
        reply_markup=phone_reply_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(bot_message_id=msg.message_id)

@router.message(UserRegisterState.phone)
async def input_phone(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    if not message.contact or not message.contact.phone_number:
        await message.delete()
        return
    await message.delete()
    phone = message.contact.phone_number
    await state.update_data(phone=phone, last_error_text=None)
    await state.set_state(UserRegisterState.department)
    await bot.delete_message(chat_id=message.chat.id, message_id=bot_message_id)
    msg = await message.answer(
        PROMPTS[UserRegisterState.department],
        reply_markup=restart_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(bot_message_id=msg.message_id)

@router.message(UserRegisterState.department)
async def input_department(message: Message, state: FSMContext, bot):
    department = message.text.strip()
    data = await state.get_data()
    bot_message_id = data["bot_message_id"]
    await message.delete()
    error_text = ""
    if not department:
        error_text = format_error_block("Department/position cannot be empty. Please try again.")
        full_text = error_text + PROMPTS[UserRegisterState.department]
        last_error = data.get("last_error_text")
        if last_error == full_text:
            return
        await bot.edit_message_text(
            full_text,
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=restart_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(last_error_text=full_text)
        return
    await state.update_data(department=department, last_error_text=None)
    data = await state.get_data()
    text = (
        "<b>Registration: Confirmation</b>\n"
        "<blockquote>"
        f"Email: {data['email']}\n"
        f"Phone: {data['phone']}\n"
        f"Department/Position: {data['department']}"
        "</blockquote>\n"
        "Please check your data above.\n\n"
        "Is everything correct?"
    )
    await state.set_state(UserRegisterState.waiting_confirm_action)
    await bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=confirm_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "confirm_register", UserRegisterState.waiting_confirm_action)
async def confirm_registration(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    await state.clear()
    await callback.answer("✅ Registration completed!")
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

    invite = await get_invite_by_code(data.get("invite_code"))
    if not invite:
        logger.error(f"Invite not found for user {user.id}")
        return

    admin_tg_id = getattr(invite, "admin_tg_id", None)
    if not admin_tg_id:
        logger.error(f"Invite {invite.code} does not have admin_tg_id set")
        return

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

    await sync_all_users_on_servers(session)

@router.callback_query(F.data == "edit_register")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    msg = await callback.message.edit_text(
        "<b>Registration:</b>\nYou need to complete registration to access the system",
        reply_markup=registration_entry_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(bot_message_id=msg.message_id, last_error_text=None)