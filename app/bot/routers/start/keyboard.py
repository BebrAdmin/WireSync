from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup

def registration_entry_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Начать регистрацию", callback_data="start_registration")
    return builder.as_markup()

def phone_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def restart_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Начать заново", callback_data="edit_register")
    return builder.as_markup()

def confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_register")
    builder.button(text="🔄 Начать заново", callback_data="edit_register")
    builder.adjust(2)
    return builder.as_markup()