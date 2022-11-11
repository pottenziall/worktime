import datetime
import logging
import tkinter
import tkinter.ttk as ttk
from datetime import date, datetime
from tkinter import messagebox, scrolledtext
from typing import Dict, List, Tuple, Optional, Union

from constants import DATE_STRING_PATTERN, WorkDay
from db import DbRW

_logger = logging.getLogger("ui")

TABLE_COLUMNS = {"date": 120, "worktime": 100, "pause": 100, "overtime": 100, "whole time": 120, "time marks": 400}
# TODO: add button for close table parents
# TODO: settings: change font size


class Window:

    def __init__(self, master: tkinter.Tk, db: DbRW):
        self.root = master
        self.db = db
        self._table_columns = TABLE_COLUMNS
        self._init_ui(self.root)
        self._fill_table()

    def ask_delete(self, entity: str) -> bool:
        return messagebox.askyesno(title="Warning", message=f"Are you sure to delete from database:\n{entity}?")

    def insert_data_to_table(self, data: List[Tuple]) -> None:
        days_data = {}
        exist = set()
        for item in sorted(data, key=lambda x: datetime.strptime(x[0], DATE_STRING_PATTERN)):
            item = list(item)
            tag = item.pop()
            item_date = datetime.strptime(item[0], "%d.%m.%Y")
            month = item_date.strftime("%B %Y")
            if month not in exist:
                self._table.insert("", tkinter.END, iid=month, text=month, open=True)
            week = str(item_date.isocalendar()[1])
            if week not in exist:
                self._table.insert(month, tkinter.END, iid=week, text=f"w{week}", open=True)
                days_data[week] = []
            exist.update([month, week])
            self._table.insert(week, tkinter.END, iid=f"data{week}{item_date.weekday()}", values=item, tags=tag)
            days_data[week].append(item[1:-1])
        self._table.update()
        self._calculate_total_values(days_data)

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
            self._table.see(f"summary{week}")

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

    def validate_input(self, full_value: str, current: str, d_status: str, ind: str) -> bool:
        if not full_value or d_status == "0":
            return True
        mask = "01.34.6789 12:15 "
        value_index = int(ind) if int(ind) < 17 else int(ind) - 6 * ((int(ind) - 11) // 6)
        mask_value = mask[value_index]
        if mask_value.isdigit() and current.isdigit():
            return True
        if mask_value in [":", ".", " "] and mask_value == current:
            return True
        _logger.warning(f'Wrong input value: "{current}" in "{full_value}"')
        return False

    def _init_ui(self, root: tkinter.Tk) -> None:
        _logger.debug("Building UI")
        self._main_frame = ttk.LabelFrame(root, text="Input date and time marks, like: 10.10.2022 07:35 15:50")
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

        self.submit_button = tkinter.Button(self._input_frame, text="SUBMIT", height=2, width=20, command=self.click_submit, font="Arial 14")
        self.submit_button.pack(pady=20)

        self._init_table(self._table_frame)

        self.settings_button = ttk.Button(self._buttons_frame, text="SETTINGS", width=15, command=self._change_settings)
        self.settings_button.grid(row=0, column=0, columns=5, padx=10, pady=25)

        self.edit_button = ttk.Button(self._buttons_frame, text="EDIT", width=15, command=self._edit_table_row)
        self.edit_button.grid(row=0, column=6, padx=10)

        self.delete_button = ttk.Button(self._buttons_frame, text="DELETE", width=15, command=self._delete_entry)
        self.delete_button.grid(row=0, column=7, padx=10)

        self.text = scrolledtext.ScrolledText(self._log_frame, width=90, height=8, font="Arial 13")
        self.text.pack(fill="both", expand=True)

    def _init_table(self, frame: tkinter.Frame) -> None:
        style = ttk.Style()
        style.configure("Treeview", rowheight=22, font=('Calibri', 11))
        self._table = ttk.Treeview(frame, columns=list(self._table_columns.keys()), height=20, style="Treeview",
                                   show=["tree", "headings"])
        y = ttk.Scrollbar(frame, orient="vertical", command = self._table.yview)
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

    def _submit(self, value: str, value_to_remove: Optional[Tuple[str, str]] = None) -> None:
        workday = WorkDay.from_string(value)
        if workday is not None:
            self.write_to_db(workday)
            if value_to_remove is not None:
                self.db.delete(value_to_remove, "worktime")
            self._fill_table()
            self.insert_default_value()

    def write_to_db(self, workday: WorkDay):
        row_filter = "date", workday.date
        found_in_db = self.db.read_with_filter(row_filter)
        if len(found_in_db) == 1:
            self.db.update(workday.db_format())
            _logger.info(f'Data has been updated in db: "{" ".join(found_in_db[0])}" -> "{workday}"')
        elif len(found_in_db) == 0:
            self.db.add(workday.db_format())
            _logger.info(f'Data has written to db: "{workday}"')
        else:
            _logger.critical(f"Wrong number of database entries found for the key '{workday.date}': {found_in_db}")

    def _fill_table(self):
        self.clear_table()
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
        self.insert_data_to_table(self.workdays)

    def _delete_entry(self):
        # TODO: only one askyesno window for many items to delete
        row_values = self.get_selected(datarow_only=True)
        if row_values is not None:
            for row_value in row_values:
                row_to_delete = "date", row_value[0]
                found_in_db = self.db.read_with_filter(row_to_delete)
                if len(found_in_db) != 1:
                    _logger.warning(f"Nothing to delete in database")
                    return
                if not self.ask_delete(str(found_in_db[0])):
                    return
                self.db.delete(row_to_delete)
            self._fill_table()

    def _edit_table_row(self) -> None:
        row_values = self.get_selected(datarow_only=True)
        if row_values is None:
            return
        db_row_data = self.db.read_with_filter(("date", row_values[0][0]), "worktime")
        edit_window = EditWindow(root=self.root)
        value_to_edit = " ".join(db_row_data[0])
        edit_window.insert_to_entry(value_to_edit)
        self.root.wait_window(edit_window.top_level)
        if edit_window.returned_value and not value_to_edit == edit_window.returned_value:
            previous_date = db_row_data[0][0]
            current_date = edit_window.returned_value.split()[0]
            if current_date != previous_date:
                self._submit(edit_window.returned_value, ("date", previous_date))
            else:
                self._submit(edit_window.returned_value)
        #self.root.wait_visibility(self.root)

    def _change_settings(self) -> None:
        settings_window = SettingsWindow(root=self.root)
        self.root.wait_window(settings_window.top_level)
        if settings_window.returned_value:
            _logger.error(settings_window.returned_value)

    def _config_table(self, table: ttk.Treeview, columns: Dict[str, int]) -> None:
        table.heading("#0", text="months")
        table.column("#0", width=170, anchor=tkinter.CENTER)
        for column, width in columns.items():
            table.column(column, width=width, anchor=tkinter.CENTER)
            table.heading(column, text=column, anchor=tkinter.CENTER)

    def insert_default_value(self):
        today = str(date.today().strftime("%d.%m.%Y"))
        self.input.delete(0, tkinter.END)
        for i in today + " ":
            self.input.insert(tkinter.END, i)

    def displaytext(self, text: str):
        self.text.insert(tkinter.END, text + "\n")
        self.text.update()


class ModalWindow:

    def __init__(self, root: tkinter.Tk) -> None:
        #self.root.wm_attributes("-disabled", True)
        self.returned_value: Union[str, Dict] = ""
        self.top_level = self._init_top(root)
        self._init_ui(self.top_level)

    def _init_top(self, root: tkinter.Tk) -> tkinter.Toplevel:
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

        submit = tkinter.Button(master, text="SUBMIT", width=20, height=3, command=lambda: self._submit(self.edit_entry.get()))
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
        vars = []
        for name in column_names:
            var = tkinter.IntVar(name=name)
            checkbutton = tkinter.Checkbutton(left_frame, text=name, variable=var)
            checkbutton.pack(padx=15, pady=2, anchor="w")
            vars.append(var)
        sep = ttk.Separator(master, orient="vertical")
        sep.pack(padx=5, pady=5, expand=True, fill="x")
        label_2 = tkinter.Label(right_frame, text="Other settings:")
        label_2.pack(padx=17, pady=3, anchor="w")
        names = ["log panel visible", "log level debug"]
        for name in names:
            var = tkinter.IntVar(name=name)
            checkbutton = tkinter.Checkbutton(right_frame, text=name, variable=var)
            checkbutton.pack(padx=15, pady=2, anchor="w")
            vars.append(var)
        button = tkinter.Button(master, text="SAVE", width=20, height=2, command=lambda: self._submit(self._get_states(vars)))
        button.pack(side="bottom", pady=20, anchor="n")

    def _get_states(self, vars: List[tkinter.IntVar]) -> Dict[str, int]:
        states = {}
        for var in vars:
            states[var._name] = var.get()
        return states

