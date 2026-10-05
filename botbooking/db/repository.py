from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from botbooking.constants import SOURCE
from botbooking.db.models import BookingRequest


class BookingRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def add_request(self, data: dict[str, str]) -> tuple[BookingRequest, bool]:
        with self.session_factory() as session:
            request = BookingRequest(
                submission_key=data["submission_key"],
                service=data["service"],
                date=data["date"],
                time=data["time"],
                name=data["name"],
                phone=data["phone"],
                source=SOURCE,
            )
            session.add(request)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                existing = session.scalar(
                    select(BookingRequest).where(
                        BookingRequest.submission_key == data["submission_key"]
                    )
                )
                if existing is None:
                    raise
                return existing, False
            return request, True

    def latest_requests(self, limit: int = 5) -> list[BookingRequest]:
        with self.session_factory() as session:
            statement = (
                select(BookingRequest).order_by(BookingRequest.id.desc()).limit(limit)
            )
            return list(session.scalars(statement))
