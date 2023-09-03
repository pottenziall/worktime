import logging
from typing import Protocol, List, Callable, Type, Optional, ContextManager

from sqlalchemy import update, orm

import constants as c
import models as m

_log = logging.getLogger(__name__)
# TODO: Create aliases for complex types


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
    def __init__(self, session_scope: Callable[[], ContextManager[orm.Session]]) -> None:
        self._session_scope: Callable[[], ContextManager[orm.Session]] = session_scope

    def read(self, *, table: Type[m.Worktime], limit: Optional[int] = None) -> List[m.Worktime]:
        query: orm.Query = orm.Query([table]).order_by(table.__mapper__.primary_key[0].desc()).limit(limit)
        with self._session_scope() as s:
            return query.with_session(s).all()

    def find_in_db(self, *, table: Type[m.Worktime], key: str) -> Optional[List[m.Worktime]]:
        with self._session_scope() as s:
            found = s.query(table).where(table.__mapper__.primary_key[0] == key).all()
            return found if found else None

    def add(self, row_dicts: List[c.RowDictData], *, table: Type[m.Worktime]) -> None:
        with self._session_scope() as s:
            s.add_all([table(**row_dict) for row_dict in row_dicts])

    def update(self, row_dicts: List[c.RowDictData], *, table: Type[m.Worktime]) -> None:
        pk_name = table.__mapper__.primary_key[0].name
        with self._session_scope() as s:
            for row_dict in row_dicts:
                stmt = update(table).where(table.__dict__[pk_name] == row_dict.pop(pk_name)).values(**row_dict)
                s.execute(stmt)

    def delete(self, row_ids: List[str], *, table: Type[m.Worktime]) -> None:
        pk_name = table.__mapper__.primary_key[0].name
        with self._session_scope() as s:
            result = s.query(table).filter(m.Worktime.__dict__[pk_name].in_(row_ids)).delete()
        assert result == len(row_ids)

    def write_to_db(self, row_dicts: List[c.RowDictData], *, table: Type[m.Worktime]) -> None:
        pk_name = table.__mapper__.primary_key[0].name
        for row_dict in row_dicts:
            with self._session_scope() as s:
                exists = s.query(table).where(table.__mapper__.primary_key[0] == row_dict[pk_name]).first()
            if exists:
                self.update([row_dict], table=table)
            else:
                self.add([row_dict], table=table)


if __name__ == "__main__":
    pass
