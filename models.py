import json
import logging
import typing as tp
from contextlib import contextmanager

from sqlalchemy import Column, Text, create_engine  # type: ignore
from sqlalchemy.orm import Session, DeclarativeBase  # type: ignore

from constants import WorkDay

DEFAULT_DB_PATH = "/home/fjr0p1/PycharmProjects/worktime/test_worktime.db"

_log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# TODO: Learn about adding methods to the class. Like date to ordinal, response to str
class Worktime(Base):
    __tablename__ = "worktime"
    date = Column(Text(8), primary_key=True, nullable=False)
    times = Column(Text(200), nullable=False)
    day_type = Column(Text(15), nullable=True)

    def as_workday(self) -> WorkDay:
        values = [getattr(self, c.name) for c in self.__table__.columns]
        return WorkDay.from_values(values)

    def as_json(self) -> str:
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return json.dumps({"table": {self.__tablename__: data}})


# TODO: add sqlalchemy echo to the settings window
engine = create_engine(f"sqlite:///{DEFAULT_DB_PATH}", echo=True)
Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> tp.Generator[tp.Any, None, None]:
    """Provides a transactional scope around a series of operations."""
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        _log.exception("Session error")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    pass
