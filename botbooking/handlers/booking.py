from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from botbooking.constants import DATES, SERVICES, TIMES
from botbooking.db.repository import BookingRepository
from botbooking.keyboards import confirmation_keyboard, options_keyboard
from botbooking.services.formatters import format_request
from botbooking.states import BookingForm

router = Router(name="booking")


async def show_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BookingForm.service)
    await message.answer(
        "Здравствуйте! Выберите услугу для записи:",
        reply_markup=options_keyboard("service", SERVICES),
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await show_start(message, state)


@router.callback_query(BookingForm.service, F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext) -> None:
    service = callback.data.split(":", 1)[1]
    await state.update_data(service=service)
    await state.set_state(BookingForm.date)
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=options_keyboard("date", DATES),
    )
    await callback.answer()


@router.callback_query(BookingForm.date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext) -> None:
    date = callback.data.split(":", 1)[1]

    if date == "Выбрать вручную":
        await state.set_state(BookingForm.manual_date)
        await callback.message.edit_text("Введите дату вручную, например: 25 мая")
        await callback.answer()
        return

    await state.update_data(date=date)
    await state.set_state(BookingForm.time)
    await callback.message.edit_text(
        "Выберите время:",
        reply_markup=options_keyboard("time", TIMES),
    )
    await callback.answer()


@router.message(BookingForm.manual_date)
async def enter_manual_date(message: Message, state: FSMContext) -> None:
    await state.update_data(date=message.text.strip())
    await state.set_state(BookingForm.time)
    await message.answer(
        "Выберите время:",
        reply_markup=options_keyboard("time", TIMES),
    )


@router.callback_query(BookingForm.time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext) -> None:
    selected_time = callback.data.split(":", 1)[1]
    await state.update_data(time=selected_time)
    await state.set_state(BookingForm.name)
    await callback.message.edit_text("Введите ваше имя:")
    await callback.answer()


@router.message(BookingForm.name)
async def enter_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Введите имя минимум из двух символов.")
        return

    await state.update_data(name=name)
    await state.set_state(BookingForm.phone)
    await message.answer("Введите телефон:")


@router.message(BookingForm.phone)
async def enter_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if len(phone) < 5:
        await message.answer("Введите корректный телефон.")
        return

    await state.update_data(phone=phone)
    data = await state.get_data()
    await state.set_state(BookingForm.confirmation)
    await message.answer(
        format_request(data, title="Проверьте заявку"),
        reply_markup=confirmation_keyboard(),
    )


@router.callback_query(BookingForm.confirmation, F.data == "confirm:restart")
async def restart_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_start(callback.message, state)


@router.callback_query(BookingForm.confirmation, F.data == "confirm:yes")
async def confirm_booking(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    admin_id: int,
    repository: BookingRepository,
) -> None:
    data = await state.get_data()
    repository.add_request(data)

    await bot.send_message(admin_id, format_request(data))
    await callback.message.edit_text(
        "Заявка принята, администратор скоро свяжется с вами."
    )
    await state.clear()
    await callback.answer("Заявка отправлена")
