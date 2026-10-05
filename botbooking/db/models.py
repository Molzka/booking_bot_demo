from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BookingRequest(Base):
    __tablename__ = "requests"
    __table_args__ = (Index("uq_requests_submission_key", "submission_key", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    service: Mapped[str] = mapped_column(String(100))
    date: Mapped[str] = mapped_column(String(100))
    time: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
