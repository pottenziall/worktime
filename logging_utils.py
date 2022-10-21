import logging
from tkinter import Tk, constants, scrolledtext


class WidgetLogger(logging.Handler):
    def __init__(self, widget: scrolledtext.ScrolledText, root_instance: Tk):
        logging.Handler.__init__(self)
        self.setLevel(logging.DEBUG)
        self.widget = widget
        self.widget.config(state='disabled')
        self.widget.tag_config("INFO", foreground="green")
        self.widget.tag_config("DEBUG", foreground="grey")
        self.widget.tag_config("WARNING", foreground="orange")
        self.widget.tag_config("ERROR", foreground="red")
        self.widget.tag_config("CRITICAL", foreground="red", underline=True)
        # self.red = self.widget.tag_configure("red", foreground="red")
        self.root_instance = root_instance

    def emit(self, record):
        if self.root_instance.children:
            self.widget.config(state='normal')
            self.widget.insert(constants.END, self.format(record) + '\n', record.levelname)
            self.widget.see(constants.END)
            self.widget.config(state='disabled')
            self.widget.update()