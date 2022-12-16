import datetime
import logging
import re
import tkinter
import tkinter.ttk as ttk
from datetime import date, datetime
from tkinter import messagebox, scrolledtext
from typing import Dict, List, Optional, Union, Any

import utils
from constants import DATE_STRING_MASK, DAY_TYPE_KEYWORDS, TIME_STRING_MASK, WorkDay
from models import Worktime, session_scope

_logger = logging.getLogger("ui")

TABLE_COLUMNS = {"date": 120, "worktime": 100, "pause": 100, "overtime": 100, "whole_time": 120, "time_marks": 400,
                 "day_type": 90}


# TODO: add button for close table parents
# TODO: settings: change font size
# TODO: edit exist entries
# TODO: sort column when click on header
# TODO: undo support
# TODO: Save settings in json file
# TODO: minsize for main window


class Window:

    def __init__(self, master: tkinter.Tk):
        self.root = master
        self._table_columns = TABLE_COLUMNS
        self._table_focus: Optional[datetime] = None
        self._init_ui(self.root)
        self._fill_table()

    @staticmethod
    def ask_delete(entity: str) -> bool:
        return messagebox.askyesno(title="Warning", message=f"Are you sure to delete from database:\n{entity}?")

    def insert_data_to_table(self, data: List[Dict]) -> None:
        self.clear_table()
        days_data = {}
        exist = set()
        for row in data:
            if row["month"] not in exist:
                self._table.insert("", tkinter.END, iid=row["month"], text=row["month"], open=True)
            if row["week"] not in exist:
                self._table.insert(row["month"], tkinter.END, iid=row["week"], text=f'w{row["week"]}', open=True)
                days_data[row["week"]] = []
            exist.update([row["month"], row["week"]])
            table_row = [row[key] for key in TABLE_COLUMNS.keys()]
            days_data[row["week"]].append(table_row[1:-2])
            table_row_iid = f'data{row["week"]}{row["weekday"]}'
            self._table.insert(row["week"], tkinter.END, iid=table_row_iid, values=table_row, tags=row["color"])
            self._table.selection_set(table_row_iid)
        self._calculate_total_values(days_data)
        if self._table_focus is not None:
            focus_week = self._table_focus.isocalendar()[1]
            focus_weekday = self._table_focus.isocalendar()[2]
            self._table.selection_set(f'data{focus_week}{focus_weekday}')
            self._table.see(f'{focus_week}')
            self._table_focus = None
        self._table.update()

    def _calculate_total_values(self, days_data: Dict[str, List]) -> None:
        for week, data_sets in days_data.items():
            result = ["Summary:"]
            for i in range(len(data_sets[0])):
                s = data_sets[0][i]
                for item in data_sets[1:]:
                    s += item[i]
                hours, remainder = divmod(int(s.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                res = f"{hours}h {minutes}m" if minutes else f"{hours}h"
                result.append(res)
            self._table.insert(week, tkinter.END, iid=f"summary{week}", values=result)
            self._table.see(f'summary{week}')

    def get_selected(self, datarow_only: bool = False) -> Optional[List]:
        select = self._table.selection()
        if select:
            if datarow_only and not select[0].startswith("data"):
                _logger.warning("Please, select data row")
                return
            values = [self._table.item(sel, option="values") for sel in select]
            return values
        _logger.warning("Please, select row in table")

    def clear_table(self):
        for i in self._table.get_children():
            self._table.delete(i)
        self._table.update()

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
            pattern = "".join(mask.split(",")[:int(ind) + 1])
            if re.match(rf"{pattern}$", full_value[:int(ind) + 1]):
                return True
        _logger.warning(f'Wrong input value: "{current}" in "{full_value}"')
        return False

    def _init_ui(self, root: tkinter.Tk) -> None:
        _logger.debug("Building UI")
        self._main_frame = ttk.LabelFrame(root, text="Input date and time marks")
        self._main_frame.pack(padx=15, pady=15, fill="both", expand=True)
        self._main_frame.rowconfigure(0, weight=1, minsize=150)
        self._main_frame.rowconfigure(1, weight=18, minsize=400)
        self._main_frame.rowconfigure(2, weight=2, minsize=100)
        self._main_frame.rowconfigure(3, weight=0)
        self._main_frame.columnconfigure(0, weight=8)

        self._input_frame = ttk.Frame(self._main_frame)
        self._input_frame.grid(row=0, column=0, sticky="nsew")

        self._table_frame = ttk.Frame(self._main_frame)
        self._table_frame.grid(row=1, column=0, sticky="nsew")

        self._buttons_frame = ttk.Frame(self._main_frame)
        self._buttons_frame.grid(row=2, column=0, sticky="nsew")

        self._log_frame = ttk.Frame(self._main_frame)
        self._log_frame.grid(row=3, column=0, sticky="nsew")

        vcmd = (self.root.register(self.validate_input), "%P", "%S", "%d", "%i")
        self.input = tkinter.Entry(self._input_frame, width=60, font="Arial 19")
        self.input.pack(padx=10, fill="both", expand=True)
        self.input.bind('<Return>', self.click_submit)
        self.insert_default_value()
        self.input.config(validatecommand=vcmd, validate="key")

        self.submit_button = tkinter.Button(self._input_frame, text="SUBMIT", height=2, width=20,
                                            command=self.click_submit, font="Arial 14")
        self.submit_button.pack(pady=20)

        self._init_table(self._table_frame)

        self.settings_button = ttk.Button(self._buttons_frame, text="SETTINGS", width=15, command=self._change_settings)
        self.settings_button.grid(row=0, column=0, columns=5, padx=10, pady=25)

        self.edit_button = ttk.Button(self._buttons_frame, text="EDIT", width=15, command=self._edit_table_row)
        self.edit_button.grid(row=0, column=6, padx=10)

        self.delete_button = ttk.Button(self._buttons_frame, text="DELETE", width=15, command=self._delete_entry)
        self.delete_button.grid(row=0, column=7, padx=10)

        self.text = scrolledtext.ScrolledText(self._log_frame, width=90, height=6, font="Arial 13")
        self.text.pack(fill="both", expand=True)

    def _init_table(self, frame: tkinter.Frame) -> None:
        style = ttk.Style()
        style.configure("Treeview", rowheight=22, font=('Calibri', 11))
        self._table = ttk.Treeview(frame, columns=list(self._table_columns.keys()), height=20, style="Treeview",
                                   show=["tree", "headings"])
        y = ttk.Scrollbar(frame, orient="vertical", command=self._table.yview)
        y.pack(side="right", fill="y")
        self._table.configure(yscrollcommand=y.set)

        self._table.tag_configure("default", background="white")
        self._table.tag_configure("green", background="honeydew")
        self._table.tag_configure("red", background="mistyrose")
        self._config_table(self._table, self._table_columns)
        self._table.pack(fill="both", expand=True)
        y.config(command=self._table.yview)

    def click_submit(self, event=None) -> None:
        value = self.input.get()
        self._submit(value)

    def _submit(self, input_value: str) -> None:
        recognized = self._recognize_values(input_value)
        if recognized is None:
            return
        self.write_to_db(recognized)
        focus_date = recognized.get("date", False)
        if focus_date and focus_date.isocalendar()[2] in [6, 7]:
            _logger.warning(f'The day being filled is a weekend: {focus_date.strftime(DATE_STRING_MASK)}')
        self._table_focus = focus_date
        self._fill_table()
        self.insert_default_value()

    def write_to_db(self, data: Dict[str, Any]):
        with session_scope() as session:
            found_in_db = session.query(Worktime).filter(Worktime.date == data["date"].toordinal()).all()

            if len(found_in_db) == 1:
                try:
                    columns = found_in_db[0].__table__.columns.keys()
                    values = [found_in_db[0].__getattribute__(column) for column in columns]
                    exist_values = self._recognize_values(" ".join(values))
                    exist_workday = WorkDay(**exist_values)
                    exist_workday.update(data)
                    time_marks = utils.time_to_str(exist_workday.times)
                except AssertionError as e:
                    _logger.error(e)
                else:
                    # TODO: create function to str db_row
                    db_row = session.query(Worktime).filter(Worktime.date == exist_workday.date.toordinal()).one()

                    if exist_workday.day_type is not None:
                        db_row.day_type = exist_workday.day_type
                    db_row.date = exist_workday.date.toordinal()
                    db_row.times = time_marks
                    # TODO: Create Worktime method to str class, results
                    _logger.info(f'The row data has been updated in db: '
                                 f'"{utils.dict_to_str(exist_values)}" -> "{utils.datetime_to_str(str(db_row.date))} '
                                 f'{db_row.times} {db_row.day_type}"')
            elif len(found_in_db) == 0:
                new_workday = WorkDay(**data)
                time_marks = utils.time_to_str(new_workday.times)
                worktime = Worktime(date=new_workday.date.toordinal(),
                                    times=time_marks,
                                    day_type=new_workday.day_type)
                session.add(worktime)
                _logger.info(f'The row data has been written to db: "{new_workday}"')
            else:
                _logger.critical(f'Wrong number of database entries found for the key "{data["date"]}": {found_in_db}')

    def _fill_table(self):
        self.workdays = []
        with session_scope() as session:
            result = session.query(Worktime).order_by(Worktime.date.desc()).limit(400).all()
            result = list(reversed(result))
        if not result:
            return
        columns = result[0].__table__.columns.keys()
        for row in result:
            values = [str(row.__getattribute__(column)) for column in columns]
            values = self._recognize_values(" ".join(values))
            workday = WorkDay(**values)
            self.workdays.append(workday.as_dict())
        self.insert_data_to_table(self.workdays)

    # TODO: Fix problem with deleting
    def _delete_entry(self):
        # TODO: only one askyesno window for many items to delete
        row_values = self.get_selected(datarow_only=True)
        if row_values is not None:
            with session_scope() as session:
                for row_value in row_values:
                    date_to_search = datetime.strptime(row_value[0], DATE_STRING_MASK)
                    found_in_db = session.query(Worktime).filter(Worktime.date == date_to_search.toordinal()).all()
                    # TODO: create function for str the Worktime instance
                    message = f"[{utils.datetime_to_str(found_in_db[0].date)}, {utils.time_to_str(found_in_db[0].times)}]"
                    if not self.ask_delete(message):
                        return
                    session.delete(found_in_db[0])
            self._fill_table()

    def _edit_table_row(self) -> None:
        row_values = self.get_selected(datarow_only=True)
        if row_values is None:
            return
        with session_scope() as session:
            date_to_search = datetime.strptime(row_values[0][0], DATE_STRING_MASK)
            found_in_db = session.query(Worktime).filter(Worktime.date == date_to_search.toordinal()).all()
            assert len(found_in_db) == 1, f"Wrong number of rows in db for the date: {row_values[0][0]}"
        if not found_in_db:
            _logger.critical(f"Table row data not found in db: {row_values[0][0]}")
            return
        edit_window = EditWindow(root=self.root)
        columns = found_in_db[0].__table__.columns.keys()
        # TODO: fromordinal date when editing
        values = [str(found_in_db[0].__getattribute__(column)) for column in columns]

        value_to_edit = " ".join(values)
        edit_window.insert_to_entry(value_to_edit)
        self.root.wait_window(edit_window.top_level)
        if edit_window.returned_value and not value_to_edit == edit_window.returned_value:
            previous_date = row_values[0][0]
            current_date = edit_window.returned_value.split()[0]
            if current_date != previous_date:
                _logger.error(f"Date editing under developing")
            else:
                self._submit(edit_window.returned_value)
        # self.root.wait_visibility(self.root)

    def _change_settings(self) -> None:
        settings_window = SettingsWindow(root=self.root)
        self.root.wait_window(settings_window.top_level)
        if settings_window.returned_value:
            _logger.error(settings_window.returned_value)

    @staticmethod
    def _config_table(table: ttk.Treeview, columns: Dict[str, int]) -> None:
        table.heading("#0", text="month")
        table.column("#0", width=170, anchor=tkinter.CENTER)
        for column, width in columns.items():
            table.column(column, width=width, anchor=tkinter.CENTER)
            table.heading(column, text=column, anchor=tkinter.CENTER)

    def insert_default_value(self):
        today = str(date.today().strftime(DATE_STRING_MASK))
        self.input.delete(0, tkinter.END)
        for i in today + " ":
            self.input.insert(tkinter.END, i)

    def displaytext(self, text: str):
        self.text.insert(tkinter.END, text + "\n")
        self.text.update()

    def _recognize_values(self, data_string: str) -> Optional[Dict]:
        try:
            values = data_string.strip().split()
            if len(values) == 0:
                _logger.error(f"Data string must include at least date, like 10.10.2022")
                raise ValueError

            date_mark = datetime.strptime(values[0], DATE_STRING_MASK) if len(
                values[0]) == 10 else datetime.fromordinal(int(values[0]))
            recognized = {"date": date_mark}

            day_type = self._recognize_day_type(data_string)
            if day_type is not None:
                recognized.update(day_type)
                return recognized

            times = self._recognize_time_marks(" ".join(values[1:]))
            if times is None:
                raise ValueError
            recognized["times"] = sorted(times)
        except ValueError:
            _logger.error(f'Wrong input value: "{data_string}"')
            return
        return recognized

    @staticmethod
    def _recognize_day_type(data_string: str) -> Optional[Dict]:
        for key, value in DAY_TYPE_KEYWORDS.items():
            if key in data_string:
                return DAY_TYPE_KEYWORDS[key]

    @staticmethod
    def _recognize_time_marks(data_string: str) -> Optional[List[datetime]]:
        try:
            values = data_string.strip().split()
            times = [datetime.strptime(value, TIME_STRING_MASK) for value in values]
        except ValueError:
            _logger.error(f'Wrong time mark values: "{data_string}"')
            return
        return times


class ModalWindow:

    def __init__(self, root: tkinter.Tk) -> None:
        # self.root.wm_attributes("-disabled", True)
        self.returned_value: Union[str, Dict] = ""
        self.top_level = self._init_top(root)
        self._init_ui(self.top_level)

    @staticmethod
    def _init_top(root: tkinter.Tk) -> tkinter.Toplevel:
        top_level = tkinter.Toplevel(root)
        top_level.geometry("600x250")
        top_level.title("Modal")
        top_level.grab_set()
        top_level.transient(root)
        return top_level

    def _init_ui(self, master: tkinter.Toplevel) -> None:
        pass

    def _submit(self, value: Union[str, Dict]) -> None:
        self.returned_value = value
        self._destroy_widgets()

    def _destroy_widgets(self) -> None:
        for widget in self.top_level.winfo_children():
            widget.destroy()
        self.top_level.destroy()


class EditWindow(ModalWindow):

    def insert_to_entry(self, text: str) -> None:
        self.edit_entry.insert(tkinter.END, text)

    def _init_ui(self, master: tkinter.Toplevel) -> None:
        master.title("Editor")
        self.edit_entry = ttk.Entry(master, width=45, font="Arial 13")
        self.edit_entry.pack(pady=25)

        submit = tkinter.Button(master, text="SUBMIT", width=20, height=3,
                                command=lambda: self._submit(self.edit_entry.get()))
        submit.pack(padx=10, pady=15, anchor="s")


class SettingsWindow(ModalWindow):

    def __init__(self, root: tkinter.Tk) -> None:
        super().__init__(root)
        self.returned_value: Dict = {}

    def _init_ui(self, master: tkinter.Toplevel) -> None:
        master.title("Settings")
        left_frame = tkinter.Frame(master)
        left_frame.pack(pady=10, padx=10, side="left", expand=True, fill="both")
        right_frame = tkinter.Frame(master)
        right_frame.pack(pady=10, padx=10, side="right", expand=True, fill="both")
        label_1 = tkinter.Label(left_frame, text="Table columns:")
        label_1.pack(padx=17, pady=3, anchor="w")
        column_names = ["time marks", "whole time", "overtime", "pause"]
        variables = []
        for name in column_names:
            var = tkinter.IntVar(name=name)
            checkbutton = tkinter.Checkbutton(left_frame, text=name, variable=var)
            checkbutton.pack(padx=15, pady=2, anchor="w")
            variables.append(var)
        sep = ttk.Separator(master, orient="vertical")
        sep.pack(padx=5, pady=5, expand=True, fill="x")
        label_2 = tkinter.Label(right_frame, text="Other settings:")
        label_2.pack(padx=17, pady=3, anchor="w")
        names = ["log panel visible", "log level debug"]
        for name in names:
            var = tkinter.IntVar(name=name)
            checkbutton = tkinter.Checkbutton(right_frame, text=name, variable=var)
            checkbutton.pack(padx=15, pady=2, anchor="w")
            variables.append(var)
        button = tkinter.Button(master, text="SAVE", width=20, height=2,
                                command=lambda: self._submit(self._get_states(variables)))
        button.pack(side="bottom", pady=20, anchor="n")

    @staticmethod
    def _get_states(variables: List[tkinter.IntVar]) -> Dict[str, int]:
        states = {}
        for var in variables:
            states[var._name] = var.get()
        return states
