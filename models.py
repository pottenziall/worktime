import logging
from contextlib import contextmanager

from sqlalchemy import Column, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_PATH = "/home/fjr0p1/PycharmProjects/worktime/test_worktime.db"

_log = logging.getLogger(__name__)
Base = declarative_base()


# TODO: Learn about adding methods to the class. Like date to ordinal, response to str
class Worktime(Base):
    __tablename__ = "worktime"
    date = Column(Text(8), primary_key=True, nullable=False)
    times = Column(Text(200), nullable=False)
    day_type = Column(Text(15), nullable=True)


# TODO: add sqlalchemy echo to the settings window
main_engine = create_engine(f"sqlite:///{DEFAULT_DB_PATH}")#, echo=True)
Base.metadata.create_all(main_engine)
DBSession = sessionmaker(binds={Base: main_engine}, expire_on_commit=False)


@contextmanager
def session_scope():
    """Provides a transactional scope around a series of operations."""
    session = DBSession()
    try:
        yield session
        session.commit()
    except Exception:
        _log.exception("Session error")
        session.rollback()
        raise
    finally:
        session.close()
