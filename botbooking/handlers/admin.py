from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from botbooking.db.repository import BookingRepository
from botbooking.services.formatters import format_requests_list

router = Router(name="admin")


@router.message(Command("requests"))
async def show_requests(
    message: Message,
    admin_id: int,
    repository: BookingRepository,
) -> None:
    if message.from_user is None or message.from_user.id != admin_id:
        await message.answer("Команда доступна только администратору.")
        return

    requests = repository.latest_requests(limit=5)
    if not requests:
        await message.answer("Заявок пока нет.")
        return

    await message.answer(format_requests_list(requests))
