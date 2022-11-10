import logging
import tkinter
import os
import json

from typing import Any, Dict

from logging_utils import WidgetLogger
from constants import DbConfig, WorkDay
from db import DbRW
from window import Window

_logger = logging.getLogger("main")
_logger.setLevel(logging.DEBUG)

#TODO: select table columns in settings
#TODO: edit table row (update data)
#TODO: add vacations
#TODO: add scrollbars
class App:
    def __init__(self, ui: Window):
        self.ui = ui
        self.ui.submit_button.config(command=self._submit)
        self.ui.edit_button.config(command=self._edit_row)
        self.ui.delete_button.config(command=self._delete_entry)

        self.ui.input.bind('<Return>', self._submit)
        self._connect_to_db()
        self._fill_table()

    def _connect_to_db(self) -> None:
        json_config = self._load_db_config()
        self.db = DbRW(DbConfig(json_config["path"], json_config["default_table"], json_config["tables"]))

    def _load_db_config(self) -> Dict[str, Any]:
        db_config_path = os.path.join(os.getcwd(), "db_config.json")
        if not os.path.isfile(db_config_path):
            _logger.error(f"Db config file not found under '{db_config_path}'")
        with open(db_config_path, encoding='utf8') as json_config:
            return json.load(json_config)
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
            _logger.info(f'Data has been updated in db: "{workday}"')
        elif len(found_in_db) == 0:
            self.db.add(workday.db_format())
            _logger.info(f'Data has written to db: "{workday}"')
        else:
            _logger.error(f"Wrong number of database entries found for the key '{workday.date}': {found_in_db}")

    def _fill_table(self):
        self.ui.clear_table()
        self.workdays = []
        # TODO: sort values from db by date
        result = self.db.read(limit=105)
        if not result:
            return
        for row in result:
            workday = WorkDay.from_string(" ".join(row))
            if workday is None:
                _logger.error(f"Wrong data in the database. Not recognized: {row}")
                continue
            self.workdays.append(workday.as_tuple())
        self.ui.insert_data_to_table(self.workdays)

    def _edit_row(self):
        row_values = self.ui.get_selected(datarow_only=True)
        if row_values is not None:
            self.ui.create_editor()


    def _delete_entry(self):
        # TODO: only one askyesno window for many items to delete
        row_values = self.ui.get_selected(datarow_only=True)
        if row_values is not None:
            for row_value in row_values:
                row_to_delete = "date", row_value[0]
                found_in_db = self.db.read_with_filter(row_to_delete)
                if len(found_in_db) != 1:
                    _logger.warning(f"Nothing to delete in database")
                    return
                if not self.ui.ask_delete(str(found_in_db[0])):
                    return
                self.db.delete(row_to_delete)
            self._fill_table()


file_handler = logging.FileHandler("worktime.log", "a", encoding="utf-8")
logging.basicConfig(
    format="%(asctime)s_%(levelname)s:%(name)s:%(lineno)d:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[file_handler],
)

root = tkinter.Tk()
root.title("Timely")
root.geometry("1200x850")
window = Window(root)

text_handler = WidgetLogger(window.text, root)
logging.getLogger("").addHandler(text_handler)
_logger.debug("Start application")
app = App(window)

root.mainloop()
app.db.close_all()
_logger.debug("Application closed")
