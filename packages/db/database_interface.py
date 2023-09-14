import logging
from contextlib import contextmanager
from typing import Protocol, List, Callable, Type, Optional, ContextManager, Generator

from sqlalchemy import update, orm, Engine
from sqlalchemy.orm import Session

import packages.db.models as m
from packages import constants as c

_log = logging.getLogger(__name__)
# TODO: Create aliases for complex types


class DbError(Exception):
    pass


class DbSessionError(DbError):
    pass


class DbReadError(DbError):
    pass


class DbInsertError(DbError):
    pass


class DbRowDeleteError(DbError):
    pass


@contextmanager
def session_scope(engine: Engine) -> Generator[Session, None, None]:
    """Provides a transactional scope around a series of operations."""
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception as e:
        _log.exception("Session error")
        session.rollback()
        raise DbSessionError from e
    finally:
        session.close()


class DbInterface(Protocol):
    def read(self, *, table: Type[m.Base], limit: Optional[int] = None) -> List[m.Base]:
        pass

    def add(self, row_dicts: List[c.RowDictData], *, table: Type[m.Base]) -> None:
        pass

    def update(self, row_dicts: List[c.RowDictData], *, table: Type[m.Base]) -> None:
        pass

    def delete(self, row_ids: List[str], *, table: Type[m.Base]) -> None:
        pass


class WorktimeSqliteDbInterface:
    def __init__(self, engine: Engine) -> None:
        self._engine: Engine = engine
        self._session_scope: Callable[[Engine], ContextManager[orm.Session]] = session_scope

    def read(self, *, table: Type[m.Worktime], limit: Optional[int] = None) -> List[m.Worktime]:
        try:
            query: orm.Query = orm.Query([table]).order_by(table.__mapper__.primary_key[0].desc()).limit(limit)
            with self._session_scope(self._engine) as s:
                return query.with_session(s).all()
        except Exception as e:
            _log.exception("Failed to read from database")
            raise DbReadError from e

    def find_in_db(self, *, table: Type[m.Worktime], key: str) -> Optional[List[m.Worktime]]:
        try:
            with self._session_scope(self._engine) as s:
                found = s.query(table).where(table.__mapper__.primary_key[0] == key).all()
                return found if found else None
        except Exception as e:
            _log.exception("Failed to read from database")
            raise DbReadError from e

    def add(self, row_dicts: List[c.RowDictData], *, table: Type[m.Worktime]) -> None:
        try:
            with self._session_scope(self._engine) as s:
                s.add_all([table(**row_dict) for row_dict in row_dicts])
        except Exception as e:
            _log.exception("Failed to add to database")
            raise DbInsertError from e

    def update(self, row_dicts: List[c.RowDictData], *, table: Type[m.Worktime]) -> None:
        try:
            pk_name = table.__mapper__.primary_key[0].name
            with self._session_scope(self._engine) as s:
                for row_dict in row_dicts:
                    stmt = update(table).where(table.__dict__[pk_name] == row_dict.pop(pk_name)).values(**row_dict)
                    s.execute(stmt)
        except Exception as e:
            _log.exception("Failed to update database rows")
            raise DbInsertError from e

    def delete(self, row_ids: List[str], *, table: Type[m.Worktime]) -> None:
        try:
            pk_name = table.__mapper__.primary_key[0].name
            with self._session_scope(self._engine) as s:
                result = s.query(table).filter(m.Worktime.__dict__[pk_name].in_(row_ids)).delete()
            assert result == len(row_ids)
        except Exception as e:
            _log.exception("Failed to delete database rows")
            raise DbRowDeleteError from e

    def write_to_db(self, row_dicts: List[c.RowDictData], *, table: Type[m.Worktime]) -> None:
        pk_name = table.__mapper__.primary_key[0].name
        for row_dict in row_dicts:
            found = self.find_in_db(table=table, key=row_dict[pk_name])
            if found:
                self.update([row_dict], table=table)
            else:
                self.add([row_dict], table=table)


if __name__ == "__main__":
    pass
