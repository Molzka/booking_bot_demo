import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from botbooking.config import load_config
from botbooking.db.database import create_session_factory, init_db
from botbooking.db.repository import BookingRepository
from botbooking.handlers import admin_router, booking_router


async def main() -> None:
    config = load_config()
    engine, session_factory = create_session_factory(config.database_url)
    init_db(engine)

    bot = Bot(token=config.bot_token)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(booking_router)
    dispatcher.include_router(admin_router)

    repository = BookingRepository(session_factory)
    await dispatcher.start_polling(
        bot,
        admin_id=config.admin_id,
        repository=repository,
    )


def run() -> None:
    asyncio.run(main())
