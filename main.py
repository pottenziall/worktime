import logging
import tkinter

from db import DbRW
from window import Window
from logging_utils import WidgetLogger

_logger = logging.getLogger("main")

# TODO: select table columns in settings
# TODO: add vacations
# TODO: add possibility to write >1 day info on time

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

db = DbRW()
window = Window(master=root, db=db)
if hasattr(window, "text"):
    text_handler = WidgetLogger(window.text, root)
    logging.getLogger("").addHandler(text_handler)
_logger.debug("Start application")

root.mainloop()
_logger.debug("Application closed")
db.close_all()
