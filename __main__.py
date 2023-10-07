from __future__ import annotations

import logging
import tkinter
from typing import TYPE_CHECKING

from packages.application import App
from packages.constants import LOG_FILE_PATH, DATE_PATTERN
from packages.db.database_interface import WorktimeSqliteDbInterface
from packages.db.models import sqlite_engine
from packages.ui.ui import Window, RowType, UiRow, UiTableConfig, UiTableColumn, TableColumnParams

if TYPE_CHECKING:
    from typing import Dict, Union

_log = logging.getLogger("main")

# TODO: Add 'refresh input value=True' option to config
# TODO: select table columns in settings
# TODO: add possibility to write >1 day info on time
# TODO: display error and warnings at start
# TODO: path to db in settings
# TODO: read config at the beginning
# TODO: use subprocess
# TODO: Load all -> update just loaded item -> Item to be focused does not exist in the table: 22.07.2022
# TODO: 'limit' in settings
# TODO: fill table order in settings

APP_NAME = "Timely"
WINDOW_GEOMETRY = "1310x900"
MAIN_TABLE_CONFIG = UiTableConfig(
    "workdays",
    [
        UiRow(RowType.DATA, rf"{DATE_PATTERN}"),
        UiRow(RowType.MONTH, r"\w{,8} \d{4}"),
        UiRow(RowType.WEEK, r"w\d{1,2}"),
        UiRow(RowType.SUMMARY, r"Summary"),
    ],
    [
        TableColumnParams(UiTableColumn.TREE, 170, ""),
        TableColumnParams(UiTableColumn.DATE, 120, "date"),
        TableColumnParams(UiTableColumn.WORKTIME, 100, "worktime"),
        TableColumnParams(UiTableColumn.PAUSES, 100, "pauses"),
        TableColumnParams(UiTableColumn.OVERTIME, 120, "overtime"),
        TableColumnParams(UiTableColumn.TIME_MARKS, 400, "time marks"),
        TableColumnParams(UiTableColumn.DAY_TYPE, 90, "day type", "w"),
    ],
)
UI_CONFIG = {"main_table": MAIN_TABLE_CONFIG}
APP_CONFIG: Dict[str, Union[int, str]] = {"max_rows": 10000}

file_handler = logging.FileHandler(LOG_FILE_PATH, "a", encoding="utf-8")
logging.basicConfig(
    format="%(asctime)s_%(levelname)s:%(name)s:%(lineno)d:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[file_handler],
)

root = tkinter.Tk()
_log.debug("Start application")
window = Window(master=root, ui_config=UI_CONFIG, title=APP_NAME, geometry=WINDOW_GEOMETRY)
app = App(app_config=APP_CONFIG, user_interface=window, db_if=WorktimeSqliteDbInterface(sqlite_engine))
root.mainloop()
_log.debug("Application closed")
