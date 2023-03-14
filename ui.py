import json
import logging
import tkinter as tk
from datetime import date
from tkinter import messagebox, scrolledtext, ttk
from typing import Dict, List, Optional, Union, Any, Protocol, Callable

from dataclasses import dataclass

import constants
import logging_utils
import utils

_log = logging.getLogger("ui")

TABLE_COLUMN_PARAMS: Dict[str, List[Dict[str, Any]]] = {
    "workdays": [
        {"iid": "date", "width": 120, "text": "date"},
        {"iid": "worktime", "width": 100, "text": "worktime"},
        {"iid": "pause", "width": 100, "text": "pause"},
        {"iid": "overtime", "width": 100, "text": "overtime"},
        # {"iid": "whole_time", "width": 120, "text": "whole time"},
        {"iid": "time_marks", "width": 400, "text": "time marks"},
        {"iid": "day_type", "width": 90, "text": "day type", "anchor": "w"},
    ]
}


# TODO: settings: change font size
# TODO: edit exist entries
# TODO: undo support
# TODO: Save settings in json file
# TODO: edit does not work
# TODO: deleting does not work (row data only)
# TODO: see selection when click toggle view


class UserInterface(Protocol):
    def fill_main_table(self, rows: List[Dict[str, Any]]) -> None:
        pass

    def set_table_focus(
        self, table: ttk.Treeview, focus_item: Optional[str] = None
    ) -> None:
        pass

    def get_variable(self, name: str) -> tk.Variable:
        pass

    def process_input_value(self, value: str) -> None:
        pass

    def set_input_validator(self, validator_func: Callable) -> None:
        pass

    def insert_default_value(self, value: str) -> None:
        pass


@dataclass(frozen=True)
class TableColumn:
    iid: str
    width: int
    text: str
    anchor: str = "center"


class Window(UserInterface):
    def __init__(self, master: tk.Tk, **kwargs):
        self.master: tk.Tk = master
        self._default_input_value: Optional[str] = None
        self._table_column_params: Optional[Dict[str, List[TableColumn]]] = None
        self._set_window_name_and_geometry(master, **kwargs)
        self._init_ui()
        self._variables: List = self._init_variables()
        # self._do_checks_and_fill_main_table(self._table)

    @staticmethod
    def _init_variables() -> List[tk.Variable]:
        _log.debug("Initialize variables for external use")
        variables = [
            tk.StringVar(name="input_value"),
            tk.StringVar(name="rows_to_be_deleted"),
            tk.StringVar(name="edited_table_row"),
            tk.BooleanVar(name="fill_table_with_all_data", value=False),
            tk.StringVar(name="change_settings"),
        ]
        return variables

    def get_variable(self, name: str) -> tk.Variable:
        for var in self._variables:
            if str(var) == name:
                return var
        raise AssertionError(f"Variable is not implemented: {name}")

    @staticmethod
    def _set_window_name_and_geometry(master: tk.Tk, **kwargs) -> None:
        title = kwargs.get("title", "App")
        x, y = kwargs.get("geometry", (1200, 900))
        _log.debug(f'Set window name to "{title}" with geometry "{x}x{y}"')
        master.title(title)
        master.geometry(f"{x}x{y}")
        master.minsize(x, y)

    @staticmethod
    def _resolve_table_column_params(
        table_column_params: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[TableColumn]]:
        table_columns = {}
        try:
            for table, column_params in table_column_params.items():
                table_column = [TableColumn(**params) for params in column_params]
                table_columns[table] = table_column
            return table_columns
        except Exception:
            _log.exception(
                f"Resolving table columns failed. Incorrect input values: {table_column_params}"
            )
            raise

    def _get_table_column_params(self, table: ttk.Treeview) -> List[TableColumn]:
        table_name = table.winfo_name()
        assert self._table_column_params is not None, "No table column params found"
        if table_name not in self._table_column_params:
            raise AssertionError(
                f"There are no params provided for the table: {table_name}"
            )
        return self._table_column_params[table_name]

    def _check_table_column_params_compatibility(
        self, table: ttk.Treeview, *, workday: constants.WorkDay
    ) -> bool:
        table_columns = self._get_table_column_params(table)
        values_to_check = [column.iid for column in table_columns]
        values_to_check.append("color")
        workday_values = workday.as_dict()
        for value in values_to_check:
            if value not in workday_values:
                _log.critical(
                    f"""Table has "{value}" column but WorkDay (db) doesn't provide a value for that.
                    WorkDay values: {workday_values.keys()}"""
                )
                return False
        return True

    def fill_main_table(self, rows: List[Dict[str, Any]]) -> None:
        self._fill_table(rows, table=self._main_table)

    # """Checks that WorkDay (db) contains all the data needed to fill the table.
    # Fills main table in case of successful verification"""
    # TODO: uncomment
    # workdays = get_db_table_data(limit=1)
    # if workdays:
    #     if self._check_table_column_params_compatibility(table, workday=workdays[0]):
    #         self._fill_table(table)
    # else:
    #     _log.warning("No data received from the database")

    @staticmethod
    def _insert_summaries(
        table: ttk.Treeview, target: str, columns: List[str], values: List[Dict]
    ) -> None:
        summary_targets = {row_values[target] for row_values in values}
        summaries: Dict[str, List] = {
            summary_target: [] for summary_target in summary_targets
        }
        for row_values in values:
            summary_values = [row_values[column] for column in columns]
            summaries[row_values[target]].append(summary_values)

        for week, summary in summaries.items():
            result = ["Summary:"]
            for i in range(len(summary[0])):
                s = summary[0][i]
                for item in summary[1:]:
                    s += item[i]
                hours, remainder = divmod(int(s.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                res = f"{hours}h {minutes}m" if minutes else f"{hours}h"
                result.append(res)
            table.insert(week, tk.END, iid=f"summary{week}", values=result)
        table.update()

    def _insert_to_table(
        self, table: ttk.Treeview, *, parents: List[str], rows_values: List[Dict]
    ) -> None:
        self.clear_table(table)
        columns = table.config("columns")[-1]
        try:
            for i, key in enumerate(parents):
                parent_key = parents[i - 1] if i > 0 else ""
                for j, row_values in enumerate(rows_values):
                    item = row_values[key]
                    parent = row_values[parent_key] if parent_key else ""
                    if not table.exists(item):
                        table.insert(parent, tk.END, iid=item, text=item, open=True)

                    if key == parents[-1]:
                        values = [row_values[column] for column in columns]
                        table.insert(
                            item,
                            tk.END,
                            iid=values[0],
                            values=values,
                            open=True,
                            tags=row_values["color"],
                        )
                table.update()
        except Exception:
            _log.exception("Failed to fill the table")
            self.clear_table(table)

    def _fill_table(
        self,
        rows: List[Dict[str, Any]],
        *,
        table: ttk.Treeview,
        focus_date: Optional[date] = None,
    ) -> None:
        self._insert_to_table(
            table=self._main_table,
            parents=["month", "week"],
            rows_values=rows,
        )
        self._insert_summaries(
            table=self._main_table,
            target="week",
            columns=constants.SUMMARY_COLUMNS,
            values=rows,
        )
        _log.debug(f"{len(rows)} db rows loaded into '{table.winfo_name()}' table")
        if focus_date is not None:
            focus_item = utils.date_to_str(focus_date, constants.DATE_STRING_MASK)
            self.set_table_focus(table, focus_item)
        else:
            self.set_table_focus(table)

    def set_table_focus(
        self, table: ttk.Treeview, focus_item: Optional[str] = None
    ) -> None:
        if focus_item and not table.exists(focus_item):
            _log.warning(f"Focusing on a non-existing table item: {focus_item}")
            focus_item = table.get_children()[-1]
        else:
            focus_item = self._get_table_data_item(table)
        self._main_table.selection_set(focus_item)
        self._main_table.see(focus_item)

    def _get_table_data_item(self, table: ttk.Treeview, item: str = "") -> str:
        """Gets 'item' from table if provided, otherwise gets very first table item"""
        children = self._main_table.get_children(item)
        if children:
            return self._get_table_data_item(table, children[0])
        else:
            return item

    @staticmethod
    def ask_delete(value: str) -> bool:
        return messagebox.askyesno(
            title="Warning", message=f"Are you sure to delete from database:\n{value}?"
        )

    @staticmethod
    def clear_table(table: ttk.Treeview):
        for i in table.get_children():
            table.delete(i)
        table.update()

    def _init_ui(self) -> None:
        _log.debug("Building UI")
        main_frame = ttk.LabelFrame(
            self.master, text="Please, input date and time marks"
        )
        main_frame.pack(padx=15, pady=15, fill="both", expand=True)
        main_frame.rowconfigure(0, weight=1, minsize=150)
        main_frame.rowconfigure(1, weight=18, minsize=400)
        main_frame.rowconfigure(2, weight=2, minsize=100)
        main_frame.rowconfigure(3, weight=0)
        main_frame.columnconfigure(0, weight=8)

        self._init_log_stuff(main_frame)
        self._init_input_stuff(main_frame)
        self._init_table_stuff(main_frame)
        self._init_buttons_stuff(main_frame)

        self.b_style = ttk.Style()
        self.b_style.configure("TButton", height=2, font="Arial 14")

    def insert_default_value(self, value: Optional[str] = None) -> None:
        if value is not None:
            self._default_input_value = value
        if self._default_input_value is None:
            raise AssertionError(
                f"Default input value must be received from a controller class"
            )
        self.input.delete(0, tk.END)
        for i in self._default_input_value + " ":
            self.input.insert(tk.END, i)

    def set_input_validator(self, validator_func: Callable) -> None:
        vcmd = (self.master.register(validator_func), "%P", "%S", "%d", "%i")
        self.input.config(validatecommand=vcmd, validate="key")

    def _init_input_stuff(self, master: ttk.LabelFrame) -> None:
        _log.debug("Initialize input panel")
        frame = ttk.Frame(master)
        frame.grid(row=0, column=0, sticky="nsew")
        self.input = ttk.Entry(
            frame,
            width=60,
            font="Arial 19",
        )
        self.input.pack(padx=10, fill="both", expand=True)
        self.input.bind("<Return>", self._submit_input_value)
        self.input.focus_set()

        self.submit_button = ttk.Button(
            frame,
            text="SUBMIT",
            style="TButton",
            width=20,
            command=self._submit_input_value,
        )
        self.submit_button.pack(pady=20, ipady=20)

    @staticmethod
    def _config_table(table: ttk.Treeview, *, columns: List[TableColumn]) -> None:
        # table.heading("#0", text="month")
        table.column("#0", width=170, anchor=tk.W)
        for column in columns:
            table.column(column.iid, width=column.width, anchor=column.anchor)
            table.heading(column.iid, text=column.text, anchor=column.anchor)

    def _init_main_table(self, master: ttk.Frame) -> None:
        name = "workdays"
        column_params = self._table_column_params[name]
        style = ttk.Style()
        style.configure("Treeview", rowheight=22, font=("Calibri", 11))
        self._main_table = ttk.Treeview(
            master,
            name=name,
            columns=[c.iid for c in column_params],
            height=20,
            style="Treeview",
            show=["tree", "headings"],
        )
        y = ttk.Scrollbar(master, orient="vertical", command=self._main_table.yview)
        y.pack(side="right", fill="y")
        self._main_table.configure(yscrollcommand=y.set)

        self._main_table.tag_configure("default", background="white")
        self._main_table.tag_configure("green", background="honeydew")
        self._main_table.tag_configure("red", background="mistyrose")
        self._config_table(self._main_table, columns=column_params)
        self._main_table.pack(fill="both", expand=True)
        y.config(command=self._main_table.yview)

    def _init_table_stuff(self, master: ttk.LabelFrame) -> None:
        _log.debug("Initialize main table")
        frame = ttk.Frame(master)
        frame.grid(row=1, column=0, sticky="nsew")
        self._table_column_params = self._resolve_table_column_params(
            TABLE_COLUMN_PARAMS
        )
        self._init_main_table(frame)

    def _toggle_table_data_view(self, table: ttk.Treeview) -> None:
        state = None
        for item in table.get_children():
            if state is None:
                state = table.item(item, "open")
                state = True if not state else False
            table.item(item, open=state)
        if state:
            self.set_table_focus(table)

    def _change_settings(self) -> None:
        settings_window = SettingsWindow(root=self.master)
        self.master.wait_window(settings_window.top_level)
        if settings_window.returned_value:
            # TODO: change the error comment
            _log.error(settings_window.returned_value)

    @staticmethod
    def _get_selected(
        table: ttk.Treeview, single_only: bool = False, data_rows_only: bool = False
    ) -> Optional[Dict[str, List]]:
        select = table.selection()
        if single_only and len(select) != 1:
            _log.warning("Please, select one row in table")
            return None
        selected = {sel: table.item(sel, option="values") for sel in select}
        if data_rows_only:
            return {
                sel: val
                for sel, val in selected.items()
                if constants.RowType.from_string("".join(val)) == constants.RowType.DATA
            }
        return selected

    def _edit_table_row(self, table: ttk.Treeview) -> None:
        selected = self._get_selected(table, single_only=True, data_rows_only=True)
        if not selected:
            return
        table_row_id, _ = selected.popitem()
        # db_row = get_row_from_db_table(row_values=values)
        # TODO: Manage case when db_row is None
        # if db_row is None:
        #    raise RuntimeError("No rows to edit")
        # value_to_edit = " ".join(db_row[0])
        value_to_edit = ""
        edit_window = EditWindow(root=self.master)
        edit_window.insert_to_entry(value_to_edit)
        self.master.wait_window(edit_window.top_level)
        if (
            edit_window.returned_value
            and not value_to_edit == edit_window.returned_value
        ):
            self.get_variable("edited_table_row").set(edit_window.returned_value)
        # previous_date = values[0]
        # current_date = edit_window.returned_value.split()[0]
        # if current_date != previous_date:
        #    _log.error(f"Date editing under developing")
        # else:
        #    process_value(edit_window.returned_value)
        _log.debug("Value has not changed")
        # self.root.wait_visibility(self.root)

    def _delete_selected_table_rows(self, table: ttk.Treeview):
        selected = self._get_selected(table, data_rows_only=True)
        if selected is not None:
            # message = f"[{utils.datetime_to_str(found_in_db[0].date)}, {utils.time_to_str(found_in_db[0].times)}]"
            values = [f"\n{val}" for val in list(selected.values())]
            if not self.ask_delete("".join(values)):
                return
            keys_to_be_deleted = ",".join(selected.keys())
            self.get_variable("rows_to_be_deleted").set(keys_to_be_deleted)
            # _log.debug(f"Db rows deleted successfully:{''.join(values)}")
            # self._fill_table(table)

    def _init_buttons_stuff(self, master: ttk.LabelFrame) -> None:
        _log.debug("Initialize buttons panel")
        frame = ttk.Frame(master)
        frame.grid(row=2, column=0, sticky="nsew")

        self.load_button = ttk.Button(
            frame, text="LOAD ALL", width=15, command=self._fill_table_with_all_db_data
        )
        self.load_button.grid(row=0, column=0, padx=10, pady=25)

        self.toggle_button = ttk.Button(
            frame,
            text="TOGGLE VIEW",
            width=15,
            command=lambda: self._toggle_table_data_view(self._main_table),
        )
        self.toggle_button.grid(row=0, column=1, padx=10, pady=25)

        self.settings_button = ttk.Button(
            frame, text="SETTINGS", width=15, command=self._change_settings
        )
        self.settings_button.grid(row=0, column=2, padx=10, pady=25)

        self.edit_button = ttk.Button(
            frame,
            text="EDIT",
            width=15,
            command=lambda: self._edit_table_row(self._main_table),
        )
        self.edit_button.grid(row=0, column=3, padx=10)

        self.delete_button = ttk.Button(
            frame,
            text="DELETE",
            width=15,
            command=lambda: self._delete_selected_table_rows(self._main_table),
        )
        self.delete_button.grid(row=0, column=4, padx=10)

    def _init_log_stuff(self, master: ttk.LabelFrame) -> None:
        _log.debug("Initialize log panel")
        frame = ttk.Frame(master)
        frame.grid(row=3, column=0, sticky="nsew")

        self.text = scrolledtext.ScrolledText(
            frame, width=90, height=6, font="Arial 13"
        )
        self.text.pack(fill="both", expand=True)
        self.text_handler = logging_utils.WidgetLogger(self.text, self.master)
        _log.addHandler(self.text_handler)

    def _get_input_value(self) -> str:
        return self.input.get()

    def _submit_input_value(self, event=None) -> None:
        value = self._get_input_value()
        self.get_variable("input_value").set(value)

    def _fill_table_with_all_db_data(self) -> None:
        self.get_variable("fill_table_with_all_data").set(True)


class ModalWindow:
    def __init__(self, root: tk.Tk) -> None:
        # self.master.wm_attributes("-disabled", True)
        self.returned_value: Union[str, Dict] = ""
        self.top_level = self._init_top(root)
        self._init_ui(self.top_level)

    @staticmethod
    def _init_top(root: tk.Tk) -> tk.Toplevel:
        top_level = tk.Toplevel(root)
        top_level.geometry("600x250")
        top_level.title("Modal")
        top_level.grab_set()
        top_level.transient(root)
        return top_level

    def _init_ui(self, master: tk.Toplevel) -> None:
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
        self.edit_entry.insert(tk.END, text)

    def _init_ui(self, master: tk.Toplevel) -> None:
        master.title("Editor")
        self.edit_entry = ttk.Entry(master, width=45, font="Arial 13")
        self.edit_entry.pack(pady=25)

        submit_b = tk.Button(
            master,
            text="SUBMIT",
            width=20,
            height=3,
            command=lambda: self._submit(self.edit_entry.get()),
        )
        submit_b.pack(padx=10, pady=15, anchor="s")


class SettingsWindow(ModalWindow):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.returned_value: Dict = {}

    def _init_ui(self, master: tk.Toplevel) -> None:
        master.title("Settings")
        left_frame = tk.Frame(master)
        left_frame.pack(pady=10, padx=10, side="left", expand=True, fill="both")
        right_frame = tk.Frame(master)
        right_frame.pack(pady=10, padx=10, side="right", expand=True, fill="both")
        label_1 = tk.Label(left_frame, text="Table columns:")
        label_1.pack(padx=17, pady=3, anchor="w")
        column_names = ["time marks", "whole time", "overtime", "pause"]
        variables = []
        for name in column_names:
            var = tk.IntVar(name=name)
            checkbutton = tk.Checkbutton(left_frame, text=name, variable=var)
            checkbutton.pack(padx=15, pady=2, anchor="w")
            variables.append(var)
        sep = ttk.Separator(master, orient="vertical")
        sep.pack(padx=5, pady=5, expand=True, fill="x")
        label_2 = tk.Label(right_frame, text="Other settings:")
        label_2.pack(padx=17, pady=3, anchor="w")
        names = ["log panel visible", "log level debug"]
        for name in names:
            var = tk.IntVar(name=name)
            checkbutton = tk.Checkbutton(right_frame, text=name, variable=var)
            checkbutton.pack(padx=15, pady=2, anchor="w")
            variables.append(var)
        button = tk.Button(
            master,
            text="SAVE",
            width=20,
            height=2,
            command=lambda: self._submit(self._get_states(variables)),
        )
        button.pack(side="bottom", pady=20, anchor="n")

    @staticmethod
    def _get_states(variables: List[tk.IntVar]) -> Dict[str, int]:
        states = {}
        for var in variables:
            states[str(var)] = var.get()
        return states

    def _submit(self, value: Union[str, Dict]) -> None:
        self.returned_value = value
        self._destroy_widgets()
        with open(constants.CONFIG_FILE_PATH, "w+", encoding="utf8") as f:
            json.dump(value, f)


if __name__ == "__main__":
    pass
