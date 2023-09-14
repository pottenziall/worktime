import logging
import re
import tkinter
from datetime import datetime
from typing import List

from packages.constants import WorkWeek, WorkDay, LOG_FILE_PATH, DATE_STRING_MASK
from packages.db.database_interface import WorktimeSqliteDbInterface
from packages.db.models import sqlite_engine, Worktime
from packages.ui.ui import Window

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
WINDOW_GEOMETRY = (1310, 900)
MAX_ROW_READ_LIMIT = 10000

file_handler = logging.FileHandler(LOG_FILE_PATH, "a", encoding="utf-8")
logging.basicConfig(
    format="%(asctime)s_%(levelname)s:%(name)s:%(lineno)d:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[file_handler],
)


class App:
    def __init__(self, *, user_interface: Window, db_if: WorktimeSqliteDbInterface) -> None:
        self._ui: Window = user_interface
        self._db_if: WorktimeSqliteDbInterface = db_if
        self._prepare_ui()

    def _prepare_ui(self) -> None:
        self._ui.insert_default_value()
        self._set_ui_variables_tracing()
        self._ui.set_input_validator(self.validate_input)
        self.fill_ui_with_workdays(limit=10)

    def _set_ui_variables_tracing(self) -> None:
        input_var = self._ui.get_variable("input_value")
        input_var.trace_variable("w", lambda *x: self.add_to_db(input_var.get()))

        rows_to_delete_var = self._ui.get_variable("rows_to_be_deleted")
        rows_to_delete_var.trace_variable("w", lambda *x: self.delete_db_rows(rows_to_delete_var.get().split(",")))

        edit_table_row_var = self._ui.get_variable("edited_table_row")
        edit_table_row_var.trace_variable("w", lambda *x: self.add_to_db(edit_table_row_var.get()))

        fill_table_with_all_data_var = self._ui.get_variable("fill_table_with_all_data")
        fill_table_with_all_data_var.trace_variable("w", lambda *x: self.fill_ui_with_workdays())

    def _prepare_data_from_db(self, limit: int = MAX_ROW_READ_LIMIT) -> List[List[WorkDay]]:
        try:
            workdays = sorted(res.as_workday() for res in self._db_if.read(table=Worktime, limit=limit))
            # group workdays by weeks
            weeks_workdays: List[List[WorkDay]] = [[]]
            current_week = workdays[0].week
            for workday in workdays:
                if current_week != workday.week:
                    weeks_workdays.append([])
                    current_week = workday.week
                weeks_workdays[-1].append(workday)
            _log.debug(f"{len(workdays)} rows from the database have been prepared")
            return weeks_workdays
        except Exception:
            _log.exception(f"Failed to prepare data from the database")
            return []

    def fill_ui_with_workdays(self, limit: int = MAX_ROW_READ_LIMIT) -> None:
        weeks_workdays = self._prepare_data_from_db(limit=limit)
        try:
            self._ui.clear_table()
            for week_workdays in weeks_workdays:
                work_week = WorkWeek(week_workdays)
                week_data = [workday.as_dict() for workday in work_week.workdays]
                self._ui.fill_main_table(week_data, parents=["month", "week"])
                self._ui.fill_main_table([work_week.summary], parents=["week"])
            _log.debug(f"All fetched database rows have been loaded into main table")
        except Exception:
            _log.exception(f"Failed to fill main table")


    def add_to_db(self, table_value: str) -> None:
        skip_update = False
        try:
            new_workday = WorkDay.from_values(table_value)
            key = new_workday.as_db()["date"]
            found_in_db = self._db_if.find_in_db(table=Worktime, key=key)
            if found_in_db is not None:
                assert len(found_in_db) == 1, f"CRITICAL: database contains {len(found_in_db)} items for '{key}' key"
                workday_from_db = found_in_db[0].as_workday()
                new_workday = workday_from_db + new_workday
                if new_workday == workday_from_db:
                    skip_update = True
            if not skip_update:
                db_row_values = new_workday.as_db()
                self._db_if.write_to_db([db_row_values], table=Worktime)
        except Exception:
            _log.exception("Adding to the database failed:")
        self._ui.insert_default_value()
        if not skip_update:
            self.fill_ui_with_workdays(limit=10)

    def delete_db_rows(self, table_ids: List[str]) -> None:
        dates = [datetime.strptime(item, DATE_STRING_MASK) for item in table_ids]
        row_ids = [str(d.toordinal()) for d in dates]
        self._db_if.delete(row_ids, table=Worktime)
        self.fill_ui_with_workdays(limit=10)
        _log.debug(f"Db rows deleted successfully: {row_ids}")

    @staticmethod
    def validate_input(full_value: str, current: str, d_status: str, ind: str) -> bool:
        if not full_value or d_status == "0":
            return True
        masks = [
            r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,\d,\d,:,\d,\d, ,\d,\d,:,\d,\d, ,\d,\d,:,\d,\d, ,\d,\d,:,\d,\d, ,\d,\d,:,\d,\d",
            r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,v,a,c,a,t,i,o,n",
            r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,o,f,f",
            r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,d,a,y, ,o,f,f",
            r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,s,i,c,k",
            r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,h,o,l,i,d,a,y",
        ]
        for mask in masks:
            pattern = "".join(mask.split(",")[: int(ind) + 1])
            if re.match(rf"{pattern}$", full_value[: int(ind) + 1]):
                return True
        _log.warning(f'Wrong input value: "{current}" in "{full_value}"')
        return False


root = tkinter.Tk()
_log.debug("Start application")
window = Window(master=root, title=APP_NAME, geometry=WINDOW_GEOMETRY)
app = App(user_interface=window, db_if=WorktimeSqliteDbInterface(sqlite_engine))
root.mainloop()
_log.debug("Application closed")
