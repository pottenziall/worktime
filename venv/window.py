import datetime
import logging
import tkinter
import tkinter.ttk as ttk
import typing

_logger = logging.getLogger(__name__)


class Window:

    def __init__(self, root: tkinter.Tk, table_columns: typing.Dict[str, int]):
        self.root = root
        self._table_columns = table_columns
        self._init_ui(self.root)

    def _init_ui(self, root: tkinter.Tk) -> None:
        self._frame = tkinter.Frame(root)
        self._frame.pack(padx=15, pady=15)

        self._input = tkinter.Entry(self._frame, width=100)
        self._input.pack(pady=20)

        today = str(datetime.date.today().strftime("%d.%m.%Y")) + " "
        self._input.insert(tkinter.END, today)

        self._b = tkinter.Button(self._frame, text="Submit")

        self._init_table(self._frame)

        self._log = tkinter.Text(self._frame, width=100)
        self._log.pack(pady=20)

    def _init_table(self, frame: tkinter.Frame) -> None:
        self._table = ttk.Treeview(frame, columns=list(self._table_columns.keys()), height=20)
        self._config_table(self._table, self._table_columns)
        self._table.pack()

    def _config_table(self, table: ttk.Treeview, columns: typing.Dict[str, int]) -> None:
        for column, width in columns.items():
            table.column(column, width=width, anchor=tkinter.CENTER)
            table.heading(column, text=column, anchor=tkinter.CENTER)

