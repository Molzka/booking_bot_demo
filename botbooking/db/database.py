from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from botbooking.db.models import Base


def create_session_factory(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    engine = create_engine(database_url, connect_args=connect_args)
    return engine, sessionmaker(engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
