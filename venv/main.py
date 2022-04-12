import logging
import re
import tkinter
import typing

from constants import *
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from window import Window

_logger = logging.getLogger(__name__)


class App:

    def __init__(self, root: tkinter.Tk):
        self.w = Window(root, TABLE_COLUMNS)
        self.w._b.bind("<1>", self._submit)

    @staticmethod
    def _recognize_input(value: str) -> typing.Optional[typing.Tuple[str, ...]]:
        pattern = "(\d\d.\d\d.\d\d\d\d) (\d{3,4}) (\d{3,4})"
        m = re.match(pattern, value)
        return m.groups() if m else None

    def get_input_data(self, value: str) -> typing.Optional[typing.Tuple[str, ...]]:
        input = self._recognize_input(value)
        if input is not None:
            return input
        else:
            _logger.debug("Wrong input data")

    def _submit(self, event) -> None:
        input_data = self.get_input_data(self.w._input.get())

        _logger.debug("Writing data do database...")

root = tkinter.Tk()
#root.geometry("zoomed")

app = App(root)

root.mainloop()