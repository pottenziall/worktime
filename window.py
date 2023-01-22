
import json
import logging
import re
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, scrolledtext, ttk
from typing import Dict, List, Optional, Union, Iterable

import constants
import utils
from models import Worktime, session_scope, DBSession

_log = logging.getLogger("ui")

DEFAULT_INPUT_VALUE = str(date.today().strftime(constants.DATE_STRING_MASK))
TABLE_COLUMNS = {"date": 120, "worktime": 100, "pause": 100, "overtime": 100, "whole_time": 120, "time_marks": 400,
                 "day_type": 90}


# TODO: settings: change font size
# TODO: edit exist entries
# TODO: undo support
# TODO: Save settings in json file
# TODO: edit does not work
# TODO: deleting does not work
# TODO: see selection when click toggle view


def submit(input_value: str) -> constants.WorkDay:
    workday = constants.WorkDay.from_values(input_value)
    write_data_to_db(workday)
    return workday


def update_db_row(session: DBSession, new: constants.WorkDay, exist: Worktime) -> None:
    values = utils.get_query_result_values(result=[exist])[0]
    exist_workday = constants.WorkDay.from_values(values)
    exist_workday.update({k: v for k, v in new.__dict__.items()})
    time_marks = utils.time_to_str(data=exist_workday.times)
    # TODO: create function to str db_row
    result = session.query(Worktime).filter(Worktime.date == exist_workday.date.toordinal()).all()
    assert len(result) == 1, f"More than one db entry found for the date: {exist_workday.date}"
    db_row = result[0]
    if exist_workday.day_type is not None:
        db_row.day_type = exist_workday.day_type
    db_row.date = exist_workday.date.toordinal()
    db_row.times = time_marks
    # TODO: Create Worktime method to str class, results
    # _log.info(f'The row data has been updated in db: '
    #  f'"{utils.dict_to_str(values)}" -> "{utils.datetime_to_str(str(db_row.date))} '
    #  f'{db_row.times} {db_row.day_type}"')


def add_to_db(session: DBSession, workday: constants.WorkDay) -> None:
    time_marks = utils.time_to_str(data=workday.times)
    table_row = Worktime(date=workday.date.toordinal(), times=time_marks, day_type=workday.day_type)
    session.add(table_row)


def write_data_to_db(workday: constants.WorkDay) -> None:
    with session_scope() as session:
        found_in_db = session.query(Worktime).filter(Worktime.date == workday.date.toordinal()).all()
        if len(found_in_db) == 1:
            update_db_row(session=session, new=workday, exist=found_in_db[0])
            message = f'Db table has been updated with next data: {workday}'
        elif len(found_in_db) == 0:
            add_to_db(session=session, workday=workday)
            message = f'Data has been written to db: {workday}'
        else:
            raise AssertionError(f"Only one db row must be found for a date, but found: {len(found_in_db)}")
    _log.info(message)


def get_db_table_data(limit: int) -> List[constants.WorkDay]:
    with session_scope() as session:
        result = session.query(Worktime).order_by(Worktime.date.desc()).limit(limit).all()
        result = list(reversed(result))
    workdays = []
    for values_set in utils.get_query_result_values(result=result):
        try:
            workday = constants.WorkDay.from_values(values_set)
        except Exception:
            _log.exception(f"Error when trying to create WorkDay instance from values:\n{values_set}\nSkipping")
        else:
            workdays.append(workday)
    return workdays


def delete_db_rows(rows: Iterable[List]) -> None:
    with session_scope() as session:
        for row in rows:
            date_to_search = datetime.strptime(row[0], constants.DATE_STRING_MASK)
            found_in_db = session.query(Worktime).filter(Worktime.date == date_to_search.toordinal()).all()
            # TODO: create function for str the Worktime instance
            session.delete(found_in_db[0])


def get_row_from_db_table(row_values: List[str]) -> Optional[List[str]]:
    with session_scope() as session:
        date_to_search = datetime.strptime(row_values[0], constants.DATE_STRING_MASK)
        found_in_db = session.query(Worktime).filter(Worktime.date == date_to_search.toordinal()).all()
        if not found_in_db:
            return None
        assert len(found_in_db) == 1, f"For the date {row_values[0]} found {len(found_in_db)} rows in db"
        values = utils.get_query_result_values(result=found_in_db)
    return values


def validate_input(full_value: str, current: str, d_status: str, ind: str) -> bool:
    if not full_value or d_status == "0":
        return True
    masks = [
        r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,\d,\d,:,\d,\d, ,\d,\d,:,\d,\d, ,\d,\d,:,\d,\d, ,\d,\d,:,\d,\d, ,\d,\d,:,\d,\d",
        r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,v,a,c,a,t,i,o,n",
        r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,o,f,f",
        r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,d,a,y, ,o,f,f",
        r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,s,i,c,k",
        r"\d,\d,.,\d,\d,.,\d,\d,\d,\d, ,h,o,l,i,d,a,y",
    ]
    for mask in masks:
        pattern = "".join(mask.split(",")[:int(ind) + 1])
        if re.match(rf"{pattern}$", full_value[:int(ind) + 1]):
            return True
    _log.warning(f'Wrong input value: "{current}" in "{full_value}"')
    return False


class Window:

    def __init__(self, master: tk.Tk):
        self.master = master
        self._init_ui()
        self._fill_table()

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
            self._table.insert(week, tk.END, iid=f"summary{week}", values=result)
        # self._table.see(f'summary{week}')

    def insert_to_table(self, workdays: List[constants.WorkDay], table: ttk.Treeview) -> List[constants.TableIid]:
        if not workdays:
            _log.warning("No data to fill the table")
            return []
        self.clear_table(table)
        iids = []
        days_data: Dict = {}
        for workday in workdays:
            row = workday.as_dict()
            month_iid = row["month"]
            if month_iid not in iids:
                table.insert("", tk.END, iid=month_iid, text=month_iid, open=True)
                iids.append(month_iid)
            week_iid = row["week"]
            if week_iid not in iids:
                table.insert(month_iid, tk.END, iid=week_iid, text=f'w{week_iid}', open=True)
                iids.append(week_iid)
                days_data[week_iid] = []
            # TODO: change approach
            table_row = [row[key] for key in TABLE_COLUMNS.keys()]
            days_data[week_iid].append(table_row[1:-2])
            table_row_iid = constants.TableIid("data", week_iid, row["weekday"])
            table.insert(week_iid, tk.END, iid=str(table_row_iid), values=table_row, tags=row["color"])
            iids.append(table_row_iid)
        self._calculate_total_values(days_data)
        table.update()
        return iids

    def _fill_table(self, focus_date: Optional[datetime] = None, limit: int = 10) -> None:
        workdays = get_db_table_data(limit)
        iids = self.insert_to_table(workdays, self._table)
        if iids:
            focus_iid = iids[-1]
            if focus_date is not None:
                focus_iid = constants.TableIid("data", focus_date.isocalendar()[1], focus_date.isocalendar()[2])
            self._table.selection_set(str(focus_iid))
            self._table.see(str(focus_iid))

    @staticmethod
    def ask_delete(value: str) -> bool:
        return messagebox.askyesno(title="Warning", message=f"Are you sure to delete from database:\n{value}?")

    @staticmethod
    def clear_table(table: ttk.Treeview):
        for i in table.get_children():
            table.delete(i)
        table.update()

    def _init_ui(self) -> None:
        _log.debug("Building UI")
        main_frame = ttk.LabelFrame(self.master, text="Input date and time marks")
        main_frame.pack(padx=15, pady=15, fill="both", expand=True)
        main_frame.rowconfigure(0, weight=1, minsize=150)
        main_frame.rowconfigure(1, weight=18, minsize=400)
        main_frame.rowconfigure(2, weight=2, minsize=100)
        main_frame.rowconfigure(3, weight=0)
        main_frame.columnconfigure(0, weight=8)

        self.b_style = ttk.Style()
        self.b_style.configure("TButton", height=2, font="Arial 14")

        self._init_input_staff(main_frame)
        self._init_table_staff(main_frame)
        self._init_buttons_staff(main_frame)
        self._init_log_staff(main_frame)

    def insert_default_value(self):
        self.input.delete(0, tk.END)
        for i in DEFAULT_INPUT_VALUE + " ":
            self.input.insert(tk.END, i)

    def _init_input_staff(self, master: ttk.LabelFrame) -> None:
        frame = ttk.Frame(master)
        frame.grid(row=0, column=0, sticky="nsew")

        vcmd = (self.master.register(validate_input), "%P", "%S", "%d", "%i")
        self.input = ttk.Entry(frame, width=60, font="Arial 19")
        self.input.pack(padx=10, fill="both", expand=True)
        self.input.bind("<Return>", self._submit)
        self.insert_default_value()
        self.input.config(validatecommand=vcmd, validate="key")
        self.input.focus_set()

        self.submit_button = ttk.Button(frame, text="SUBMIT", style="TButton", width=20, command=self._submit)
        self.submit_button.pack(pady=20, ipady=20)

    @staticmethod
    def _config_table(table: ttk.Treeview, columns_config: Dict[str, int]) -> None:
        table.heading("#0", text="month")
        table.column("#0", width=170, anchor=tk.LEFT)
        for column, width in columns_config.items():
            table.column(column, width=width, anchor=tk.CENTER)
            table.heading(column, text=column, anchor=tk.CENTER)

    def _init_table(self, master: tk.Frame) -> None:
        style = ttk.Style()
        style.configure("Treeview", rowheight=22, font=('Calibri', 11))

        self._table = ttk.Treeview(master, columns=list(TABLE_COLUMNS.keys()), height=20, style="Treeview",
                                   show=["tree", "headings"])
        y = ttk.Scrollbar(master, orient="vertical", command=self._table.yview)
        y.pack(side="right", fill="y")
        self._table.configure(yscrollcommand=y.set)

        self._table.tag_configure("default", background="white")
        self._table.tag_configure("green", background="honeydew")
        self._table.tag_configure("red", background="mistyrose")
        self._config_table(table=self._table, columns_config=TABLE_COLUMNS)
        self._table.pack(fill="both", expand=True)
        y.config(command=self._table.yview)

    def _init_table_staff(self, master: ttk.LabelFrame) -> None:
        frame = ttk.Frame(master)
        frame.grid(row=1, column=0, sticky="nsew")

        self._init_table(frame)

    def _load_all_db_data(self) -> None:
        self._fill_table(limit=10000)

    @staticmethod
    def _toggle_table_view(table: ttk.Treeview) -> None:
        state = None
        for item in table.get_children():
            if state is None:
                state = table.item(item, "open")
                state = True if not state else False
            table.item(item, open=state)
            table.see(item)

    def _change_settings(self) -> None:
        settings_window = SettingsWindow(root=self.master)
        self.master.wait_window(settings_window.top_level)
        if settings_window.returned_value:
            # TODO: change the error comment
            _log.error(settings_window.returned_value)

    def get_selected(self, single_only: bool = False, datarows_only: bool = False) -> Optional[Dict[str, List]]:
        select = self._table.selection()
        if single_only and len(select) != 1:
            _log.warning("Please, select one row in table")
            return None
        selected = {sel: self._table.item(sel, option="values") for sel in select}
        if datarows_only:
            return {sel: val for sel, val in selected.items() if
                    constants.RowType.from_string("".join(val)) == constants.RowType.DATA}
        return selected

    def _edit_table_row(self) -> None:
        selected = self.get_selected(single_only=True, datarows_only=True)
        if not selected:
            return
        _, values = selected.popitem()
        db_row = get_row_from_db_table(row_values=values)[0]
        value_to_edit = " ".join(db_row)

        edit_window = EditWindow(root=self.master)
        edit_window.insert_to_entry(value_to_edit)
        self.master.wait_window(edit_window.top_level)
        if edit_window.returned_value and not value_to_edit == edit_window.returned_value:
            previous_date = values[0]
            current_date = edit_window.returned_value.split()[0]
            if current_date != previous_date:
                _log.error(f"Date editing under developing")
            else:
                submit(edit_window.returned_value)
        _log.debug("Value has not changed")
        # self.root.wait_visibility(self.root)

    def _delete_table_rows(self):
        selected = self.get_selected(datarows_only=True)
        if selected is not None:
            # message = f"[{utils.datetime_to_str(found_in_db[0].date)}, {utils.time_to_str(found_in_db[0].times)}]"
            values = [f'\n{val}' for val in list(selected.values())]
            if not self.ask_delete("".join(values)):
                return
            delete_db_rows(selected.values())
            _log.debug(f"Db rows deleted successfully:{''.join(values)}")
            self._fill_table()

    def _init_buttons_staff(self, master: ttk.LabelFrame) -> None:
        frame = ttk.Frame(master)
        frame.grid(row=2, column=0, sticky="nsew")

        self.load_button = ttk.Button(frame, text="LOAD ALL", width=15, command=self._load_all_db_data)
        self.load_button.grid(row=0, column=0, padx=10, pady=25)

        self.collapse_button = ttk.Button(frame, text="TOGGLE VIEW", width=15, command=lambda: self._toggle_table_view(
            self._table))
        self.collapse_button.grid(row=0, column=1, padx=10, pady=25)

        self.settings_button = ttk.Button(frame, text="SETTINGS", width=15, command=self._change_settings)
        self.settings_button.grid(row=0, column=2, padx=10, pady=25)

        self.edit_button = ttk.Button(frame, text="EDIT", width=15, command=self._edit_table_row)
        self.edit_button.grid(row=0, column=3, padx=10)

        self.delete_button = ttk.Button(frame, text="DELETE", width=15, command=self._delete_table_rows)
        self.delete_button.grid(row=0, column=4, padx=10)

    def _init_log_staff(self, master: ttk.LabelFrame) -> None:
        frame = ttk.Frame(master)
        frame.grid(row=3, column=0, sticky="nsew")

        self.text = scrolledtext.ScrolledText(frame, width=90, height=6, font="Arial 13")
        self.text.pack(fill="both", expand=True)

    def _submit(self, event=None) -> None:
        try:
            value = self.input.get()
            workday = submit(value)
            if hasattr(workday, "date") and workday.date.isocalendar()[2] in [6, 7]:
                _log.warning(f'The day being filled is a weekend: {workday.date.strftime(constants.DATE_STRING_MASK)}')
            if workday is not None:
                self._fill_table(focus_date=workday.date)
                self.insert_default_value()
        except Exception:
            _log.exception("Error:")


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

        submit_b = tk.Button(master, text="SUBMIT", width=20, height=3,
                             command=lambda: self._submit(self.edit_entry.get()))
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
        button = tk.Button(master, text="SAVE", width=20, height=2,
                           command=lambda: self._submit(self._get_states(variables)))
        button.pack(side="bottom", pady=20, anchor="n")

    @staticmethod
    def _get_states(variables: List[tk.IntVar]) -> Dict[str, int]:
        states = {}
        for var in variables:
            states[var._name] = var.get()
        return states

    def _submit(self, value: Union[str, Dict]) -> None:
        self.returned_value = value
        self._destroy_widgets()
        with open(constants.CONFIG_FILE_PATH, "w+", encoding='utf8') as f:
            json.dump(value, f)


if __name__ == "__main__":
    pass
