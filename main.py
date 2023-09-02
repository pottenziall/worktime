import logging
import re
import tkinter
import typing as tp
from datetime import date, datetime

import constants
import database_interface
import models
import ui

_log = logging.getLogger("main")

# TODO: select table columns in settings
# TODO: add possibility to write >1 day info on time
# TODO: display error and warnings at start
# TODO: path to db in settings
# TODO: read config at the beginning
# TODO: use subprocess
# TODO: Load all -> update just loaded item -> Item to be focused does not exist in the table: 22.07.2022
# TODO: 'limit' in settings

LOG_FILENAME = "worktime.log"
APP_NAME = "Timely"
WINDOW_GEOMETRY = (1310, 900)
DEFAULT_INPUT_VALUE = str(date.today().strftime(constants.DATE_STRING_MASK))
MAX_ROW_READ_LIMIT = 10000

file_handler = logging.FileHandler(LOG_FILENAME, "a", encoding="utf-8")
logging.basicConfig(
    format="%(asctime)s_%(levelname)s:%(name)s:%(lineno)d:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[file_handler],
)


class App:
    def __init__(
        self,
        *,
        user_interface: ui.Window,
        db_if: database_interface.WorktimeSqliteDbInterface,
    ) -> None:
        self._ui: ui.Window = user_interface
        self._db_if: database_interface.WorktimeSqliteDbInterface = db_if
        self._prepare_ui()

    def _prepare_ui(self) -> None:
        self._ui.insert_default_value(DEFAULT_INPUT_VALUE)
        self._set_ui_vars_tracing()
        self._ui.set_input_validator(self.validate_input)
        self.fill_ui_with_workdays(limit=10)

    def _set_ui_vars_tracing(self) -> None:
        input_var = self._ui.get_variable("input_value")
        input_var.trace_variable("w", lambda *x: self.add_to_db(input_var.get()))

        rows_to_delete_var = self._ui.get_variable("rows_to_be_deleted")
        rows_to_delete_var.trace_variable(
            "w",
            lambda *x: self.delete_db_rows(rows_to_delete_var.get().split(",")),
        )

        edit_table_row_var = self._ui.get_variable("edited_table_row")
        edit_table_row_var.trace_variable(
            "w", lambda *x: self.add_to_db(edit_table_row_var.get())
        )

        fill_table_with_all_data_var = self._ui.get_variable("fill_table_with_all_data")
        fill_table_with_all_data_var.trace_variable(
            "w", lambda *x: self.fill_ui_with_workdays()
        )

    def fill_ui_with_workdays(self, limit: int = MAX_ROW_READ_LIMIT) -> None:
        result = self._db_if.read(table=models.Worktime, limit=limit)
        workdays = [res.as_workday() for res in result]
        workdays_dict_values = [workday.as_dict() for workday in workdays]
        self._ui.fill_main_table(workdays_dict_values)

    def add_to_db(self, table_value: str) -> None:
        skip_update = False
        try:
            new_workday = constants.WorkDay.from_values(table_value)
            key = new_workday.as_db()["date"]
            found_in_db = self._db_if.find_in_db(table=models.Worktime, key=key)
            if found_in_db is not None:
                assert len(found_in_db) == 1, f"CRITICAL: database contains {len(found_in_db)} items for '{key}' key"
                workday_from_db = found_in_db[0].as_workday()
                new_workday = workday_from_db + new_workday
                if new_workday == workday_from_db:
                    skip_update = True
            if not skip_update:
                db_row_values = new_workday.as_db()
                self._db_if.write_to_db([db_row_values], table=models.Worktime)
        except Exception:
            _log.exception("Adding to the database failed:")
        self._ui.insert_default_value(DEFAULT_INPUT_VALUE)
        if not skip_update:
            self.fill_ui_with_workdays(limit=10)

    def delete_db_rows(self, table_ids: tp.List[str]) -> None:
        dates = [
            datetime.strptime(item, constants.DATE_STRING_MASK) for item in table_ids
        ]
        row_ids = [str(d.toordinal()) for d in dates]
        self._db_if.delete(row_ids, table=models.Worktime)
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


if __name__ == "__main__":
    root = tkinter.Tk()
    _log.debug("Start application")
    window = ui.Window(master=root, title=APP_NAME, geometry=WINDOW_GEOMETRY)
    app = App(
        user_interface=window,
        db_if=database_interface.WorktimeSqliteDbInterface(models.session_scope),
    )
    root.mainloop()
    _log.debug("Application closed")
