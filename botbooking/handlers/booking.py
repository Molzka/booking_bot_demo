import logging
from datetime import datetime, tzinfo
from uuid import uuid4

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from botbooking.constants import DATES, SERVICES, TIMES
from botbooking.db.repository import BookingRepository
from botbooking.keyboards import confirmation_keyboard, options_keyboard
from botbooking.services.formatters import format_request
from botbooking.services.validation import is_future_slot, normalize_phone, parse_booking_date
from botbooking.states import BookingForm

router = Router(name="booking")
logger = logging.getLogger(__name__)
DATE_PROMPT = "Введите дату текстом в формате ДД.ММ.ГГГГ, например 25.05.2030."
PHONE_PROMPT = "Введите телефон текстом с кодом страны, например +7 999 123-45-67."
STALE_BUTTON = "Эта кнопка устарела. Используйте последнее сообщение бота или /start."


async def answer_callback(callback: CallbackQuery, text: str | None = None) -> None:
    try:
        await callback.answer(text)
    except TelegramAPIError as error:
        logger.warning("Callback acknowledgement failed: %s", type(error).__name__)


async def current_choice(
    callback: CallbackQuery, state: FSMContext, prefix: str, values: dict[str, str]
) -> str | None:
    data = await state.get_data()
    parts = (callback.data or "").split(":")
    message = callback.message
    if (
        not isinstance(message, Message)
        or message.chat.type != "private"
        or message.chat.id != callback.from_user.id
        or message.message_id != data.get("button_message_id")
        or len(parts) != 3
        or parts[0] != prefix
        or parts[1] != data.get("button_token")
        or parts[2] not in values
    ):
        await answer_callback(callback, STALE_BUTTON)
        return None
    return values[parts[2]]


async def show_options(
    message: Message, state: FSMContext, step: State, prefix: str,
    values: list[str], prompt: str, *, edit: bool = False,
) -> None:
    token = uuid4().hex
    send = message.edit_text if edit else message.answer
    sent = await send(prompt, reply_markup=options_keyboard(prefix, values, token))
    await state.update_data(button_token=token, button_message_id=sent.message_id)
    await state.set_state(step)


def choices(values: list[str]) -> dict[str, str]:
    return {str(index): value for index, value in enumerate(values)}


async def show_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(submission_key=uuid4().hex)
    await show_options(
        message, state, BookingForm.service, "service", SERVICES,
        "Здравствуйте! Выберите услугу для записи.\n"
        "Отменить заполнение: /cancel. Начать заново: /start.",
    )


@router.message(F.chat.type != "private")
async def private_chat_only(message: Message) -> None:
    command = (message.text or "").split(maxsplit=1)
    if command and command[0].split("@")[0] in ("/start", "/cancel"):
        await message.answer("Для записи откройте личный чат с ботом и отправьте /start.")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await show_start(message, state)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Заполнение отменено. Для новой записи отправьте /start.")


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message) -> None:
    await message.answer("Неизвестная команда. Начать заново: /start. Отменить: /cancel.")


@router.callback_query(BookingForm.service, F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext) -> None:
    service = await current_choice(callback, state, "service", choices(SERVICES))
    if service is None:
        return
    await state.update_data(service=service)
    await show_options(
        callback.message, state, BookingForm.date, "date", DATES, "Выберите дату:", edit=True
    )
    await answer_callback(callback)


@router.callback_query(BookingForm.date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, booking_timezone: tzinfo) -> None:
    value = await current_choice(callback, state, "date", choices(DATES))
    if value is None:
        return
    if value == "Выбрать вручную":
        await callback.message.edit_text(DATE_PROMPT)
        await state.set_state(BookingForm.manual_date)
    else:
        selected = parse_booking_date(value, datetime.now(booking_timezone).date())
        await state.update_data(date=selected)
        await show_options(
            callback.message, state, BookingForm.time, "time", TIMES, "Выберите время:", edit=True
        )
    await answer_callback(callback)


@router.message(BookingForm.manual_date, F.text)
async def enter_manual_date(message: Message, state: FSMContext, booking_timezone: tzinfo) -> None:
    try:
        selected = parse_booking_date(message.text, datetime.now(booking_timezone).date())
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(date=selected)
    await show_options(message, state, BookingForm.time, "time", TIMES, "Выберите время:")


@router.callback_query(BookingForm.time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext, booking_timezone: tzinfo) -> None:
    selected = await current_choice(callback, state, "time", choices(TIMES))
    if selected is None:
        return
    data = await state.get_data()
    if not is_future_slot(data["date"], selected, datetime.now(booking_timezone)):
        await answer_callback(callback, "Это время уже прошло. Выберите более позднее время или /start.")
        return
    await callback.message.edit_text("Введите ваше имя текстом:")
    await state.update_data(time=selected)
    await state.set_state(BookingForm.name)
    await answer_callback(callback)


@router.message(BookingForm.name, F.text)
async def enter_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not 2 <= len(name) <= 120 or not any(char.isalpha() for char in name):
        await message.answer("Введите имя текстом: от 2 до 120 символов, с буквами.")
        return
    await state.update_data(name=name)
    await state.set_state(BookingForm.phone)
    await message.answer(PHONE_PROMPT)


@router.message(BookingForm.phone, F.text)
async def enter_phone(message: Message, state: FSMContext) -> None:
    try:
        phone = normalize_phone(message.text)
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(phone=phone)
    data = await state.get_data()
    token = uuid4().hex
    sent = await message.answer(
        format_request(data, title="Проверьте заявку"), reply_markup=confirmation_keyboard(token)
    )
    await state.update_data(button_token=token, button_message_id=sent.message_id)
    await state.set_state(BookingForm.confirmation)


@router.callback_query(BookingForm.confirmation, F.data.startswith("confirm:"))
async def confirm_booking(
    callback: CallbackQuery, state: FSMContext, bot: Bot, admin_id: int,
    repository: BookingRepository, booking_timezone: tzinfo,
) -> None:
    action = await current_choice(callback, state, "confirm", {"yes": "yes", "restart": "restart"})
    if action is None:
        return
    if action == "restart":
        await show_start(callback.message, state)
        await answer_callback(callback)
        return
    data = await state.get_data()
    if not is_future_slot(data["date"], data["time"], datetime.now(booking_timezone)):
        await state.set_data({"service": data["service"], "submission_key": data["submission_key"]})
        await show_options(
            callback.message, state, BookingForm.date, "date", DATES,
            "Выбранное время уже прошло. Выберите дату заново:", edit=True,
        )
        await answer_callback(callback)
        return
    try:
        request, created = repository.add_request(data)
    except SQLAlchemyError as error:
        logger.error("Booking save failed: %s", type(error).__name__)
        await answer_callback(callback, "Не удалось сохранить заявку. Нажмите подтверждение ещё раз.")
        return

    # The commit is final. Telegram failures cannot leave this form retryable.
    await state.clear()
    try:
        await callback.message.edit_text("Заявка принята, администратор скоро свяжется с вами.")
    except TelegramAPIError as error:
        logger.warning("Receipt delivery failed for request %s: %s", request.id, type(error).__name__)
    await answer_callback(callback, "Заявка принята")
    if created:
        try:
            await bot.send_message(admin_id, format_request(data))
        except TelegramAPIError as error:
            logger.warning("Admin notification failed for request %s: %s", request.id, type(error).__name__)


@router.callback_query()
async def stale_callback(callback: CallbackQuery) -> None:
    await answer_callback(callback, STALE_BUTTON)


@router.message(StateFilter(BookingForm))
async def unexpected_input(message: Message, state: FSMContext) -> None:
    prompts = {
        BookingForm.service.state: "Выберите услугу кнопкой в последнем сообщении бота.",
        BookingForm.date.state: "Выберите дату кнопкой в последнем сообщении бота.",
        BookingForm.manual_date.state: DATE_PROMPT,
        BookingForm.time.state: "Выберите время кнопкой в последнем сообщении бота.",
        BookingForm.name.state: "Введите ваше имя текстом.",
        BookingForm.phone.state: PHONE_PROMPT,
        BookingForm.confirmation.state: "Проверьте заявку и нажмите кнопку подтверждения.",
    }
    await message.answer(prompts[await state.get_state()] + " Отменить: /cancel.")


@router.message()
async def no_active_booking(message: Message) -> None:
    await message.answer("Для записи отправьте /start.")
