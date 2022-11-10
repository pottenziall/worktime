import datetime
import time
import logging
import tkinter
import tkinter.ttk as ttk
from datetime import date, datetime
from tkinter import messagebox
from typing import Dict, List, Tuple, Optional
from constants import DATE_STRING_PATTERN
from functools import reduce
from operator import add

_logger = logging.getLogger(__name__)

TABLE_COLUMNS = {"date": 120, "worktime": 100, "pause": 100, "overtime": 100, "whole time": 120, "time marks": 400}


class Window:

    def __init__(self, root: tkinter.Tk):
        self.root = root
        self._table_columns = TABLE_COLUMNS
        self._init_ui(self.root)

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
            self._table.insert(week, tkinter.END, values=result)
            self._table.update()

    def create_editor(self):
        #self.root.wm_attributes("-disabled", True)
        modal = tkinter.Toplevel(self.root)
        modal.geometry("400x300")
        modal.grab_set()

        entry = ttk.Entry(modal, width=100)
        entry.pack()

        submit = tkinter.Button(modal, text="SUBMIT", command=modal.destroy)
        submit.pack(padx=10)
        self.root.wait_window(modal)
        self.root.wait_visibility()
        self.root.grab_set()
        modal.transient(self.root)

    def get_selected(self, datarow_only: bool = False) -> Optional[List]:
        select = self._table.selection()
        if select:
            if datarow_only and not select[0].startswith("data"):
                _logger.warning("Please, select data row")
                return
            values = [self._table.item(sel, option="values") for sel in select]
            return values
        _logger.debug("Please, select row in table")

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
        _logger.warning(f"Wrong input value: {current}, {full_value}")
        return False

    def _init_ui(self, root: tkinter.Tk) -> None:
        self._main_frame = ttk.LabelFrame(root, text="Input date and time marks, like: 10.10.2022 07:35 15:50")
        self._main_frame.pack(padx=15, pady=15, fill="both", expand=True)

        self._input_frame = ttk.Frame(self._main_frame)
        self._input_frame.pack()

        self._table_frame = ttk.Frame(self._main_frame)
        self._table_frame.pack(fill="both", expand=True)

        self._buttons_frame = ttk.Frame(self._main_frame)
        self._buttons_frame.pack(fill="both", expand=True)

        self._log_frame = ttk.Frame(self._main_frame)
        self._log_frame.pack(fill="both", expand=True)

        vcmd = (self.root.register(self.validate_input), "%P", "%S", "%d", "%i")
        self.input = tkinter.Entry(self._input_frame, width=300)
        self.input.pack(padx=10, fill="both", expand=True)
        self.insert_default_value()
        self.input.config(validatecommand=vcmd, validate="key")

        self.submit_button = tkinter.Button(self._input_frame, text="SUBMIT", height=2, width=25)
        self.submit_button.pack(pady=10)

        self._init_table(self._table_frame)

        self.options_button = ttk.Button(self._buttons_frame, text="SETTINGS", width=15)
        self.options_button.grid(row=0, column=0, columns=5, padx=10)

        self.edit_button = ttk.Button(self._buttons_frame, text="EDIT", width=15)
        self.edit_button.grid(row=0, column=6, padx=10)

        self.delete_button = ttk.Button(self._buttons_frame, text="DELETE", width=15)
        self.delete_button.grid(row=0, column=7, padx=10)

        self.text = tkinter.Text(self._log_frame, width=110)
        self.text.pack(pady=20, fill="both", expand=True)

    def _init_table(self, frame: tkinter.Frame) -> None:
        self._table = ttk.Treeview(frame, columns=list(self._table_columns.keys()), height=20,
                                   show=["tree", "headings"])
        self._table.tag_configure("default", background="white")
        self._table.tag_configure("green", background="honeydew")
        self._table.tag_configure("red", background="mistyrose")
        self._config_table(self._table, self._table_columns)
        self._table.pack(pady=15, fill="both", expand=True)


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
            self.input.insert(tkinter.END, i)  # 09:00 12:00 13:00 19:00")

    def displaytext(self, text: str):
        self.text.insert(tkinter.END, text + "\n")
        self.text.update()

    def get_input_value(self) -> str:
        return self.input.get()
