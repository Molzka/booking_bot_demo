from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def options_keyboard(prefix: str, values: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value in values:
        builder.button(text=value, callback_data=f"{prefix}:{value}")
    builder.adjust(1)
    return builder.as_markup()


def confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Подтвердить заявку", callback_data="confirm:yes")
    builder.button(text="Заполнить заново", callback_data="confirm:restart")
    builder.adjust(1)
    return builder.as_markup()
