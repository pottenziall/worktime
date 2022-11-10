import logging
import os
import sqlite3
from typing import List, Optional, Tuple

from constants import DbConfig

_logger = logging.getLogger(__name__)


class DbRW:
    def __init__(self, config: DbConfig):
        self._config = config
        self._create_connection(config)

    def _is_db_new(self) -> bool:
        if not os.path.getsize(self._db_path):
            return True
        return False

    def _create_connection(self, config: DbConfig):
        self._db_path = config.path
        try:
            self._connect = sqlite3.connect(self._db_path)
            self._cursor = self._connect.cursor()
        except sqlite3.OperationalError:
            _logger.exception(f"Something wrong with connection to the db: {self._db_path}")
        else:
            if self._is_db_new():
                _logger.warning(f"Database '{self._db_path}' is new. Parsing config and recreating tables in db")
                self._parse_config(config)
            _logger.info(
                f"""Connected to the database "{self._db_path}", size: {os.path.getsize(self._db_path) / 1024} KB""")

    def _parse_config(self, config: DbConfig):
        _logger.debug("Creating database tables")
        for table, columns in config.tables.items():
            col_params = []
            for column, column_type in columns:
                col_params.append(f"{column} {column_type}")
            statement = f"""CREATE TABLE IF NOT EXISTS {table} ({",".join(col_params)});"""
            _logger.debug(f"Executing statement: {statement}")
            self._cursor.execute(statement)
        self._connect.commit()

    def reconnect(self):
        if self._connect and self._cursor:
            self.close_all()
        _logger.warning("Reconnecting to database")
        self._create_connection(self._config)

    def close_all(self):
        self._cursor.close()
        self._connect.close()
        _logger.info("Database connection closed")

    def add(self, data: Tuple, table: Optional[str] = None):
        table = self._config.default_table if table is None else table
        columns, values = data
        statement = f"""INSERT INTO {table}{columns} VALUES{values};"""
        _logger.debug(f"Executing statement: {statement}")
        self._connect.execute(statement)
        self._connect.commit()

    def update(self, data: Tuple, table: Optional[str] = None):
        table = self._config.default_table if table is None else table
        columns, values = data
        data_columns = columns[1:] if len(columns) > 2 else columns[1]
        data_values = values[1:] if len(values) > 2 else values[1]
        statement = f"""UPDATE {table} SET {data_columns}="{data_values}" WHERE {columns[0]}="{values[0]}";"""
        _logger.debug(f"Executing statement: {statement}")
        self._cursor.execute(statement)
        self._connect.commit()

    def read_with_filter(self, row_filter: Tuple[str, str], table: Optional[str] = None) -> List[Tuple[str]]:
        table = self._config.default_table if table is None else table
        column, value = row_filter
        statement = f"""SELECT * FROM {table} WHERE {column}="{value}";"""
        return self._read(statement)

    def read(self, table: Optional[str] = None, limit: int = 10000) -> List[Tuple[str]]:
        table = self._config.default_table if table is None else table
        statement = f"SELECT * FROM {table} LIMIT {limit};"
        return self._read(statement)

    def _read(self, statement: str) -> List[Tuple[str, ...]]:
        _logger.debug(f"Executing statement: {statement}")
        self._cursor.execute(statement)
        return self._cursor.fetchall()

    def delete(self, row_filter: Tuple[str, ...], table: Optional[str] = None):
        table = self._config.default_table if table is None else table
        column, value = row_filter
        statement = f"""DELETE FROM {table} WHERE {column}="{value}";"""
        _logger.debug(f"Executing statement: {statement}")
        self._cursor.execute(statement)
        self._connect.commit()
        _logger.debug(f"Database entry with key {column}={value} has been deleted")


if __name__ == '__main__':
    pass
