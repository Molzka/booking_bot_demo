from collections.abc import Mapping, Sequence

from botbooking.constants import SOURCE
from botbooking.db.models import BookingRequest


def format_request(data: Mapping[str, str], title: str = "Новая заявка") -> str:
    return (
        f"{title}\n\n"
        f"Услуга: {data['service']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Источник: {SOURCE}"
    )


def format_requests_list(requests: Sequence[BookingRequest]) -> str:
    blocks = []
    for request in requests:
        created_at = request.created_at.strftime("%Y-%m-%d %H:%M")
        blocks.append(
            f"#{request.id} от {created_at}\n"
            f"Услуга: {request.service}\n"
            f"Дата: {request.date}\n"
            f"Время: {request.time}\n"
            f"Имя: {request.name}\n"
            f"Телефон: {request.phone}\n"
            f"Источник: {request.source}"
        )

    return "Последние 5 заявок:\n\n" + "\n\n".join(blocks)
