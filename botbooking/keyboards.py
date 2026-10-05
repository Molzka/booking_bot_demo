from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def options_keyboard(prefix: str, values: list[str], token: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, value in enumerate(values):
        builder.button(text=value, callback_data=f"{prefix}:{token}:{index}")
    builder.adjust(1)
    return builder.as_markup()


def confirmation_keyboard(token: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Подтвердить заявку", callback_data=f"confirm:{token}:yes")
    builder.button(text="Заполнить заново", callback_data=f"confirm:{token}:restart")
    builder.adjust(1)
    return builder.as_markup()
