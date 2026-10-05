import re
from datetime import date, datetime, time, timedelta


def parse_booking_date(value: str, today: date) -> str:
    value = value.strip()
    if value in ("Сегодня", "Завтра"):
        selected = today + timedelta(days=value == "Завтра")
    else:
        if not re.fullmatch(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", value):
            raise ValueError("Введите дату в формате ДД.ММ.ГГГГ, например 25.05.2030.")
        try:
            selected = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Такой даты нет в календаре. Введите дату в формате ДД.ММ.ГГГГ.") from None
    if selected < today:
        raise ValueError("Эта дата уже прошла. Выберите сегодня или будущую дату.")
    return selected.isoformat()


def is_future_slot(selected_date: str, selected_time: str, now: datetime) -> bool:
    slot = datetime.combine(
        date.fromisoformat(selected_date), time.fromisoformat(selected_time), tzinfo=now.tzinfo
    )
    return slot > now


def normalize_phone(value: str) -> str:
    value = value.strip()
    error = "Введите телефон с кодом страны, например +7 999 123-45-67."
    if not re.fullmatch(r"\+?[0-9 ()-]+", value):
        raise ValueError(error)
    phone = re.sub(r"[ ()-]", "", value)
    if re.fullmatch(r"[78][0-9]{10}", phone):
        phone = "+7" + phone[1:]
    if not re.fullmatch(r"\+[1-9][0-9]{7,14}", phone):
        raise ValueError(error)
    if phone.startswith("+7") and len(phone) != 12:
        raise ValueError("Номер с кодом +7 должен содержать 11 цифр.")
    return phone
