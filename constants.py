import enum
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date, time
from typing import Dict, List, Any, Union, Tuple

import utils

_log = logging.getLogger(__name__)

CONFIG_FILE_PATH = "/home/fjr0p1/PycharmProjects/worktime/config.json"
DEFAULT_WORKDAY_TIMEDELTA = timedelta(hours=8)
ANY_DATE = date(2023, 1, 1)
DATE_STRING_MASK = "%d.%m.%Y"
TIME_STRING_MASK = "%H:%M"
DATE_PATTERN = r"\d\d.\d\d.\d\d\d\d"
ORDINAL_DATE_PATTERN = r"\d{6}"
TIME_PATTERN = r"\d\d:\d\d"
DAY_TYPE_KEYWORDS = {
    "vacation": {
        "day_type": "vacation",
        "times": [datetime.strptime("08:00", TIME_STRING_MASK).time(),
                  datetime.strptime("16:00", TIME_STRING_MASK).time()]},
    "off": {
        "day_type": "day off",
        "times": []},
    "day off": {
        "day_type": "day off",
        "times": []},
    "sick": {
        "day_type": "sick leave",
        "times": [datetime.strptime("08:00", TIME_STRING_MASK).time(),
                  datetime.strptime("16:00", TIME_STRING_MASK).time()]},
    "holiday": {
        "day_type": "holiday",
        "times": [datetime.strptime("08:00", TIME_STRING_MASK).time(),
                  datetime.strptime("16:00", TIME_STRING_MASK).time()]},
}
TABLE_ROW_TYPES = {"month": r"\w{,8} \d{4}", "data": rf"{DATE_PATTERN}", "week": r"w\d{1,2}", "summary": r"Summary"}
TABLE_COLUMNS: List[Tuple[Any, ...]] = [
    ("date", 120, "date"),
    ("worktime", 100, "worktime"),
    ("pause", 100, "pause"),
    ("overtime", 100, "overtime"),
   # ("whole_time", 120, "whole time"),
    ("time_marks", 400, "time marks"),
    ("day_type", 90, "day type", "w"),
]
SUMMARY_COLUMNS = ["worktime", "pause", "overtime", "whole_time"]


@dataclass
class TableColumn:
    iid: str
    width: int
    text: str
    anchor: str = "center"


class RowType(enum.Enum):
    DATA = "data"
    MONTH = "month"
    WEEK = "week"
    SUMMARY = "summary"

    @classmethod
    def from_string(cls, value: str) -> "RowType":
        for iid_type, pattern in TABLE_ROW_TYPES.items():
            if re.search(pattern, value):
                return RowType(iid_type)
        raise ValueError(f"Row not recognized: {value}")


@dataclass
class WorkDay:
    date: date
    times: List[time] = field(default_factory=list)
    day_type: str = ""

    @staticmethod
    def _recognize_day_type(value_str: str) -> Dict:
        for key, value in DAY_TYPE_KEYWORDS.items():
            if key == value_str:
                return value
        raise ValueError(f"Day type not recognized: {value_str}")

    @staticmethod
    def _recognize_time_marks(values: List[str]) -> List[time]:
        try:
            marks = {datetime.strptime(value, TIME_STRING_MASK).time() for value in values}
            return list(sorted(marks))
        except ValueError:
            _log.exception(f"Incorrect time mark values: {values}")
            raise

    @classmethod
    def from_values(cls, input_values: Union[List, str]) -> "WorkDay":
        try:
            values = input_values if isinstance(input_values, str) else " ".join(input_values)

            date_values = re.findall(f"{DATE_PATTERN}|{ORDINAL_DATE_PATTERN}", values)
            if len(date_values) != 1:
                raise ValueError(f"Input value must include one date mark. Found {len(date_values)}: {date_values}")
            date_mark = datetime.strptime(date_values[0], DATE_STRING_MASK).date() if len(
                date_values[0]) == 10 else datetime.fromordinal(int(date_values[0])).date()

            time_values = re.findall(TIME_PATTERN, values)
            day_type_values = re.findall("|".join(DAY_TYPE_KEYWORDS.keys()), values)
            if time_values and not day_type_values:
                time_values = cls._recognize_time_marks(time_values)
                return WorkDay(date=date_mark, times=time_values)
            elif day_type_values and not time_values:
                rest_args = cls._recognize_day_type(day_type_values[0])
                return WorkDay(date=date_mark, **rest_args)
            elif day_type_values and time_values:
                times = cls._recognize_time_marks(time_values)
                for item in DAY_TYPE_KEYWORDS[day_type_values[0]]["times"]:
                    if item not in times:
                        raise ValueError(
                            f'Inconsistency of input values: the day type "{day_type_values[0]}" does not match time marks: {times}')
                rest_args = cls._recognize_day_type(day_type_values[0])
                return WorkDay(date=date_mark, **rest_args)
            else:
                raise ValueError(f"Input values must include at least one time mark or a day type: {values}")
        except ValueError:
            _log.exception(f'Wrong input values: "{input_values}"')
            raise

    def update(self, data: Dict[str, Any]) -> None:
        date_instance = utils.date_to_str(self.date)
        assert data.get("date"), f'Data to update must include "date" key: {data}. WorkDay has not updated'
        assert self.date == data["date"], f'Exist WorkDay\'s can\'t be updated with data that has the different date:' \
                                          f' {data["date"]} and {self.date}. WorkDay has not updated'
        if data.get("day_type"):
            _log.warning(
                f'For the date "{date_instance}", time marks will be replaced in db because the new "{data["day_type"]}" day type'
                f' received: {utils.time_to_str(self.times, braces=True)} -> {utils.time_to_str(data["times"], braces=True)}')
            self.times = data["times"]
            self.day_type = data["day_type"]
        elif not data.get("day_type", False) and self.day_type:
            self.day_type = ""
            _log.warning(
                f'For the date "{date_instance}", time marks will be replaced in db: {utils.time_to_str(self.times, braces=True)} '
                f'-> {utils.time_to_str(data["times"], braces=True)}')
            self.times = data["times"]
        elif not data.get("day_type", False) and not self.day_type:
            times = set(self.times)
            times.update(data["times"])
            self.times = sorted(list(times))
            _log.debug(
                f'For the date "{date_instance}", existing time marks and new ones are combined. '
                f'Result: {utils.time_to_str(self.times, braces=True)}')
        else:
            _log.critical("Caught unhandled error")

    @property
    def color(self) -> str:
        if any([
            self.worktime < DEFAULT_WORKDAY_TIMEDELTA,
            self.whole_time == timedelta(seconds=0),
        ]):
            return "red"
        elif self.overtime > timedelta(0):
            return "green"
        return "default"

    def as_dict(self) -> Dict[str, Any]:
        data = dict(week="week" + " " + str(self.date.isocalendar()[1]),
                    month=self.date.strftime("%B %Y"),
                    date=self.date.strftime(DATE_STRING_MASK),
                    weekday=self.date.isocalendar()[2],
                    worktime=self.worktime,
                    pause=self.pauses,
                    overtime=self.overtime,
                    whole_time=self.whole_time,
                    time_marks=[time_mark.strftime(TIME_STRING_MASK) for time_mark in self.times],
                    color=self.color,
                    day_type=self.day_type
                    )
        if self.worktime + self.pauses + self.overtime != self.whole_time:
            _log.critical(f"Sum (worktime + pauses + overtime) != whole time")
        return data

    def __str__(self):
        time_marks = utils.time_to_str(self.times)
        return f'{self.date.strftime(DATE_STRING_MASK)} {time_marks} {self.day_type if self.day_type else ""}'

    @property
    def whole_time(self) -> timedelta:
        if len(self.times) < 2:
            return timedelta(0)
        diff = datetime.combine(ANY_DATE, self.times[-1]) - datetime.combine(ANY_DATE, self.times[0])
        return diff

    @property
    def pauses(self) -> timedelta:
        if len(self.times) < 2:
            return timedelta(0)
        pauses = timedelta(seconds=0)
        for i in range(1, len(self.times) - 1, 2):
            pause = datetime.combine(ANY_DATE, self.times[i + 1]) - datetime.combine(ANY_DATE, self.times[i])
            pauses += pause
        return pauses

    @property
    def worktime(self) -> timedelta:
        if len(self.times) < 2:
            return timedelta(0)
        worktime = self.whole_time - self.pauses
        return worktime if worktime <= DEFAULT_WORKDAY_TIMEDELTA else DEFAULT_WORKDAY_TIMEDELTA

    @property
    def overtime(self):
        if len(self.times) < 2:
            return timedelta(0)
        worktime = self.whole_time - self.pauses
        if worktime > DEFAULT_WORKDAY_TIMEDELTA:
            return worktime - DEFAULT_WORKDAY_TIMEDELTA
        else:
            return timedelta(seconds=0)
