from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def logs_menu_keyboard(level, mode, page, total_pages):
    nav_buttons = [
        InlineKeyboardButton(text="⬅️ Prev", callback_data="logs_prev"),
        InlineKeyboardButton(text="Next ➡️", callback_data="logs_next"),
    ]
    if mode == "Freeze":
        nav_buttons.append(InlineKeyboardButton(text="🔄 Refresh", callback_data="logs_refresh"))

    level_text = {
        "INFO": "🟢 INFO",
        "WARNING": "🟡 WARNING",
        "ERROR": "🔴 ERROR",
        "ALL": "📋 ALL"
    }[level]
    level_button = InlineKeyboardButton(text=level_text, callback_data="logs_level_switch")
    download_button = InlineKeyboardButton(text="⬇️ Download", callback_data="logs_download")
    mode_button = InlineKeyboardButton(
        text="▶️ Live" if mode == "Freeze" else "⏸ Freeze",
        callback_data="logs_mode_toggle"
    )
    second_row = [level_button, download_button, mode_button]

    back_button = InlineKeyboardButton(text="⬅️ Back", callback_data="logs_back")

    keyboard = [
        nav_buttons,
        second_row,
        [back_button],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def close_file_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Close", callback_data=f"close_file_{user_id}")]
        ]
    )