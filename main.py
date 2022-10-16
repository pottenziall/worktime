import logging
import tkinter

import logging_utils
from constants import DB_CONFIG, DbConfig, TABLE_COLUMNS, WorkDay
from db import DbRW
from window import Window

_logger = logging.getLogger("main")
_logger.setLevel(logging.DEBUG)


class App:

    def __init__(self, ui: Window):
        self.ui = ui
        self.ui.submit_button.config(command=self._submit)
        self.ui.delete_button.config(command=self._delete_entry)
        self.ui.input.bind('<Return>', self._submit)
        self.db = DbRW(DbConfig(DB_CONFIG["path"], DB_CONFIG["default_table"], DB_CONFIG["tables"]))
        self._fill_table()

    def _submit(self, event=None) -> None:
        value = self.ui.get_input_value()
        workday = WorkDay.from_string(value)
        if workday is not None:
            self.write_to_db(workday)
            self._fill_table()
            self.ui.insert_default_value()

    def write_to_db(self, workday: WorkDay):
        row_filter = "date", workday.date
        found_in_db = self.db.read_with_filter(row_filter)
        if len(found_in_db) == 1:
            exist_time_marks = found_in_db[0][1].split()
            workday.update(exist_time_marks)
            self.db.update(workday.db_format())
            _logger.debug(f"Data has been updated in db: '{workday}'")
        elif len(found_in_db) == 0:
            self.db.add(workday.db_format())
            _logger.debug(f"Data has written to db: '{workday}'")
        else:
            _logger.error(f"Wrong number of database entries found for the key '{workday.date}': {found_in_db}")

    def _fill_table(self):
        self.ui.clear_table()
        self.workdays = []
        # TODO: sort values from db by date
        for row in self.db.read(limit=15):
            workday = WorkDay.from_string(" ".join(row))
            if workday is None:
                _logger.error(f"Wrong data in the database. Not recognized: {row}")
                continue
            self.workdays.append(workday.as_tuple())
        self.ui.insert_to_table(self.workdays)

    def _delete_entry(self):
        # TODO: only one askyesno window for many items to delete
        table_values = self.ui.get_selected()
        for table_value in table_values:
            row_to_delete = "date", table_value[0]
            found_in_db = self.db.read_with_filter(row_to_delete)
            if len(found_in_db) != 1:
                _logger.error(f"Wrong number of database entries found for the key '{table_value[0]}': {found_in_db}")
            if self.ui.ask_delete(str(found_in_db[0])):
                self.db.delete(row_to_delete)
        self._fill_table()


file_handler = logging.FileHandler("worktime.log", "a", encoding="utf-8")
logging.basicConfig(
    format="%(asctime)s_%(levelname)s:%(name)s:%(lineno)d:%(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[file_handler],
)

root = tkinter.Tk()
root.geometry("1200x850")
window = Window(root, TABLE_COLUMNS)

text_handler = logging_utils.WidgetLogger(window.text, root)
logging.getLogger("").addHandler(text_handler)
_logger.info("Start application")
app = App(window)

root.mainloop()
app.db.close_all()
_logger.info("Application closed")
