import datetime
import logging
import tkinter
import tkinter.ttk as ttk
from datetime import date, datetime
from tkinter import messagebox
from typing import Dict, List, Tuple

_logger = logging.getLogger(__name__)


class Window:

    def __init__(self, root: tkinter.Tk, table_columns: Dict[str, int]):
        self.root = root
        self._table_columns = table_columns
        self._init_ui(self.root)

    def ask_delete(self, entity: str) -> bool:
        return messagebox.askyesno(title="Warning", message=f"Are you sure to delete from database:\n{entity}?")

    def insert_to_table(self, data: List[Tuple]):
        # TODO: sorted months in table
        months = set()
        for item in data:
            item = list(item)
            tag = item.pop()
            item_date = datetime.strptime(item[0], "%d.%m.%Y")
            month = item_date.strftime("%B %Y")
            if month not in months:
                self._table.insert("", tkinter.END, iid=month, text=month, open=True)
                months.add(month)
            self._table.insert(month, tkinter.END, values=item, tags=tag)
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
        if not full_value:
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
        self._table.tag_configure("green", background="DarkSeaGreen3")
        self._table.tag_configure("red", background="pink")
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
