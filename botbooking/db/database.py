from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from botbooking.db.models import Base, BookingRequest


def create_session_factory(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    engine = create_engine(database_url, connect_args=connect_args)
    return engine, sessionmaker(engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("requests")}
        if "submission_key" not in columns:
            connection.execute(text("ALTER TABLE requests ADD COLUMN submission_key VARCHAR(32)"))
        for index in BookingRequest.__table__.indexes:
            index.create(connection, checkfirst=True)
