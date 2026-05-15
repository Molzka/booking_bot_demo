from aiogram.fsm.state import State, StatesGroup


class BookingForm(StatesGroup):
    service = State()
    date = State()
    manual_date = State()
    time = State()
    name = State()
    phone = State()
    confirmation = State()
