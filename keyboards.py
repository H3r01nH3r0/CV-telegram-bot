from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def start() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("Send pictures!")
    return markup


def upload_pictures() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("I have sent all pictures")
    markup.row("Cancel")
    return markup


def from_list_len(list_len: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for i in range(1, list_len + 1):
        markup.add(InlineKeyboardButton(text=i, callback_data=f"story_index={i}"))

    markup.add(InlineKeyboardButton(text="Cancel", callback_data="cancel"))
    return markup


def cancel() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Cancel", callback_data="cancel"))
    return markup


def close() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Close", callback_data="close"))
    return markup
