import logging
import tkinter

from logging_utils import WidgetLogger
from window import Window

_logger = logging.getLogger("main")

# TODO: select table columns in settings
# TODO: add possibility to write >1 day info on time
# TODO: display error and warnings at start
# TODO: path to db in settings
# TODO: read config at the beginning
# TODO: use subprocess

LOG_FILENAME = "worktime.log"
file_handler = logging.FileHandler(LOG_FILENAME, "a", encoding="utf-8")
logging.basicConfig(
    format="%(asctime)s_%(levelname)s:%(name)s:%(lineno)d:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[file_handler],
)

root = tkinter.Tk()
root.title("Timely")
root.geometry("1310x900")
root.minsize(1310, 900)

window = Window(master=root)
if hasattr(window, "text"):
    text_handler = WidgetLogger(window.text, root)
    logging.getLogger("").addHandler(text_handler)
_logger.debug("Start application")

root.mainloop()
_logger.debug("Application closed")
