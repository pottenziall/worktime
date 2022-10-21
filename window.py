import datetime
import logging
import tkinter
import tkinter.ttk as ttk
from datetime import date, datetime
from tkinter import messagebox
from typing import Dict, List, Tuple
from constants import DEFAULT_WORKDAY_TIMEDELTA
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
        for item in sorted(data):
            item = list(item)
            tag = item.pop()
            item_date = datetime.strptime(item[0], "%d.%m.%Y")
            month = item_date.strftime("%B %Y")
            if month not in exist:
                self._table.insert("", tkinter.END, iid=month, text=month, open=True)
            week = str(item_date.isocalendar()[1])
            if week not in exist:
                self._table.insert(month, tkinter.END, iid=week, text=f"week {week}", open=True)
                days_data[week] = []
            exist.update([month, week])
            self._table.insert(week, tkinter.END, values=item, tags=tag)
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

    def get_selected(self):
        select = self._table.selection()
        values = [self._table.item(sel, option="values") for sel in select]
        return values

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
        self._frame = tkinter.Frame(root)
        self._frame.pack(padx=15, pady=15)

        entry_label = tkinter.Label(self._frame, anchor='w',
                                    text="Input date and time marks, like: 10.10.2022 07:35 15:50", width=90)
        entry_label.pack()

        vcmd = (self.root.register(self.validate_input), "%P", "%S", "%d", "%i")
        self.input = tkinter.Entry(self._frame, width=90)
        self.input.pack()
        self.insert_default_value()
        self.input.config(validatecommand=vcmd, validate="key")

        self.submit_button = ttk.Button(self._frame, text="Submit", width=20)
        self.submit_button.pack(pady=5)

        self._init_table(self._frame)

        self.delete_button = ttk.Button(self._frame, text="Delete", width=15)
        self.delete_button.pack(pady=10)

        self.text = tkinter.Text(self._frame, width=110)
        self.text.pack(pady=20)

    def _init_table(self, frame: tkinter.Frame) -> None:
        self._table = ttk.Treeview(frame, columns=list(self._table_columns.keys()), height=20,
                                   show=["tree", "headings"])
        self._table.tag_configure("default", background="white")
        self._table.tag_configure("green", background="honeydew")
        self._table.tag_configure("red", background="mistyrose")
        self._config_table(self._table, self._table_columns)
        self._table.pack(pady=15)

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
