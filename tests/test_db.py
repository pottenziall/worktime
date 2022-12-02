import logging

import pytest

import constants

_logger = logging.getLogger(__name__)

MAIN_TABLE = constants.TABLES[0][0]
VALID_ROW_EXAMPLES = [
    # "(table, date, start, end, pause)"
    (MAIN_TABLE, ("11111111111", "0700", "1600", "1")),
    (MAIN_TABLE, ("01111111", "700", "1600", "130")),
    (MAIN_TABLE, ("2222222", "700", "1600")),
]
COMMON_FILTER = ("end", "1600")
WRONG_ROW_EXAMPLES = [
    (MAIN_TABLE, ("111111", "0700", "1600", "100")),
    (MAIN_TABLE, ("11111111", "2500", "700", "1")),
    (MAIN_TABLE, ("11111111", "700", "1600", "170")),
    ("woday", ("11111111", "700", "1600", "120")),
]


@pytest.fixture(scope="class")
def db(tmpdir_factory):
    db_path = tmpdir_factory.mktemp("db").join('database.db')
    db = DbRW(db_path, constants.TABLES)
    yield db
    db.close_all()


@pytest.fixture(scope="session", params=VALID_ROW_EXAMPLES)
def valid_table(request):
    name, data = request.param
    return Table(name, [WorkDay(*data)])


@pytest.fixture(scope="session", params=WRONG_ROW_EXAMPLES)
def wrong_table(request):
    name, data = request.param
    return Table(name, [WorkDay(*data)])


class TestCrudDb:
    def test_create_new_db(self, db):
        assert db, "database is not created"

    def test_insert_valid_row(self, db, valid_table):
        db.add(valid_table)

    def test_insert_wrong_row(self, db, wrong_table):
        with pytest.raises(Exception):
            db.add(wrong_table)

    def test_read_row_with_filter(self, db):
        db.read_with_filter(MAIN_TABLE, COMMON_FILTER)
