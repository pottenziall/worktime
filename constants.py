import enum
import logging
import re
from datetime import datetime, timedelta, date, time
from typing import Dict, List, Any, Union, Optional

from dataclasses import dataclass, field

from utils import date_to_str, time_to_str

_log = logging.getLogger(__name__)

RowDictData = Dict[str, str]
CONFIG_FILE_PATH = "/home/fjr0p1/PycharmProjects/worktime/config.json"
DEFAULT_WORKDAY_TIMEDELTA = timedelta(hours=8)
ANY_DATE = date(2023, 1, 1)
DATE_STRING_MASK = "%d.%m.%Y"
TIME_STRING_MASK = "%H:%M"
DATE_PATTERN = r"\d\d.\d\d.\d\d\d\d"
ORDINAL_DATE_PATTERN = r"\d{6}"
TIME_PATTERN = r"\d\d:\d\d"
DAY_TYPE_KEYWORDS: Dict[str, Any] = {
    "vacation": {
        "day_type": "vacation",
        "times": [
            datetime.strptime("08:00", TIME_STRING_MASK).time(),
            datetime.strptime("16:00", TIME_STRING_MASK).time(),
        ],
    },
    "off": {"day_type": "day off", "times": []},
    "day off": {"day_type": "day off", "times": []},
    "sick": {
        "day_type": "sick leave",
        "times": [
            datetime.strptime("08:00", TIME_STRING_MASK).time(),
            datetime.strptime("16:00", TIME_STRING_MASK).time(),
        ],
    },
    "holiday": {
        "day_type": "holiday",
        "times": [
            datetime.strptime("08:00", TIME_STRING_MASK).time(),
            datetime.strptime("16:00", TIME_STRING_MASK).time(),
        ],
    },
}
TABLE_ROW_TYPES = {
    "month": r"\w{,8} \d{4}",
    "data": rf"{DATE_PATTERN}",
    "week": r"w\d{1,2}",
    "summary": r"Summary",
}
SUMMARY_COLUMNS = ["worktime", "pause", "overtime", "whole_time"]


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
    def _recognize_date(string_value: str) -> date:  # type: ignore
        date_values = re.findall(f"{DATE_PATTERN}|{ORDINAL_DATE_PATTERN}", string_value)
        if len(date_values) != 1:
            raise ValueError(
                f"Input string value must include one date mark. Found {len(date_values)}: {date_values}"
            )
        try:
            date_instance = datetime.strptime(date_values[0], DATE_STRING_MASK).date()
        except ValueError:
            try:
                date_instance = datetime.fromordinal(int(date_values[0])).date()
            except ValueError:
                _log.exception(f"Wrong date string value: {date_values[0]}")
                raise
            else:
                return date_instance
        else:
            return date_instance

    @staticmethod
    def _recognize_time_marks(string_value: str) -> List[time]:
        try:
            time_values = re.findall(TIME_PATTERN, string_value)
            time_marks = {
                datetime.strptime(value, TIME_STRING_MASK).time()
                for value in time_values
            }
            return list(sorted(time_marks))
        except ValueError:
            _log.exception(f"Incorrect time string value: {string_value}")
            raise

    @staticmethod
    def _recognize_day_type(string_value: str) -> Optional[Dict]:
        day_type_values = re.findall("|".join(DAY_TYPE_KEYWORDS.keys()), string_value)
        if len(day_type_values) == 0:
            return None
        elif len(day_type_values) == 1:
            for day_type, params in DAY_TYPE_KEYWORDS.items():
                if day_type == day_type_values[0]:
                    return params
            raise AssertionError(
                f'Day type params not found for "{day_type_values[0]}"'
            )
        else:
            raise RuntimeError(f"More than one day type recognized: {day_type_values}")

    @classmethod
    def from_values(cls, input_values: Union[List[str], str]) -> "WorkDay":
        string_value = (
            input_values if isinstance(input_values, str) else " ".join(input_values)
        )
        date_instance = cls._recognize_date(string_value)
        time_marks = cls._recognize_time_marks(string_value)
        day_type_params = cls._recognize_day_type(string_value)

        if time_marks and not day_type_params:
            return WorkDay(date=date_instance, times=time_marks)
        elif day_type_params and not time_marks:
            return WorkDay(date=date_instance, **day_type_params)
        elif day_type_params and time_marks:
            day_type = day_type_params["day_type"]
            for item in DAY_TYPE_KEYWORDS[day_type]["times"]:
                if item not in time_marks:
                    raise ValueError(
                        f'Inconsistency of input values: the day type "{day_type}" does not match time marks: {time_marks}"'
                    )
            return WorkDay(date=date_instance, **day_type_params)
        else:
            raise ValueError(
                f"Input value must include at least one date and either time mark or day type or both: {string_value}"
            )

    def update(self, data: Dict[str, Any]) -> None:
        date_instance = date_to_str(self.date)
        assert data.get(
            "date"
        ), f'Data to update must include "date" key: {data}. WorkDay has not updated'
        assert self.date == data["date"], (
            f"Exist WorkDay's can't be updated with data that has the different date:"
            f' {data["date"]} and {self.date}. WorkDay has not updated'
        )
        if data.get("day_type"):
            _log.warning(
                f'For "{date_instance}", time marks will be replaced in db because the new "{data["day_type"]}" day type'
                f' received: {time_to_str(self.times, braces=True)} -> {time_to_str(data["times"], braces=True)}'
            )
            self.times = data["times"]
            self.day_type = data["day_type"]
        elif not data.get("day_type", False) and self.day_type:
            self.day_type = ""
            _log.warning(
                f'For the date "{date_instance}", time marks will be replaced in db: {time_to_str(self.times, braces=True)}'
                f'-> {time_to_str(data["times"], braces=True)}'
            )
            self.times = data["times"]
        elif not data.get("day_type", False) and not self.day_type:
            times = set(self.times)
            times.update(data["times"])
            self.times = sorted(list(times))
            _log.debug(
                f'For the date "{date_instance}", existing time marks and new ones are combined. '
                f"Result: {time_to_str(self.times, braces=True)}"
            )
        else:
            _log.critical("Caught unhandled error")

    @property
    def color(self) -> str:
        if any(
            [
                self.worktime < DEFAULT_WORKDAY_TIMEDELTA,
                self.whole_time == timedelta(seconds=0),
            ]
        ):
            return "red"
        elif self.overtime > timedelta(0):
            return "green"
        return "default"

    def as_dict(self) -> Dict[str, Any]:
        data = dict(
            week="week" + " " + str(self.date.isocalendar()[1]),
            month=self.date.strftime("%B %Y"),
            date=self.date.strftime(DATE_STRING_MASK),
            weekday=self.date.isocalendar()[2],
            worktime=self.worktime,
            pause=self.pauses,
            overtime=self.overtime,
            whole_time=self.whole_time,
            time_marks=[
                time_mark.strftime(TIME_STRING_MASK) for time_mark in self.times
            ],
            color=self.color,
            day_type=self.day_type,
        )
        if self.worktime + self.pauses + self.overtime != self.whole_time:
            _log.critical(f"Sum (worktime + pauses + overtime) != whole time")
        return data

    def as_db(self) -> RowDictData:
        values = {
            "date": str(self.date.toordinal()),
            "times": time_to_str(self.times, TIME_STRING_MASK),
            "day_type": self.day_type,
        }
        return values

    def warn_if_weekend_day(self) -> None:
        if self.date.isocalendar()[2] in [6, 7]:
            _log.warning(
                f"The day being filled is a weekend: {self.date.strftime(DATE_STRING_MASK)}"
            )

    def __str__(self):
        time_marks = time_to_str(self.times)
        return f'{self.date.strftime(DATE_STRING_MASK)} {time_marks} {self.day_type if self.day_type else ""}'

    @property
    def whole_time(self) -> timedelta:
        if len(self.times) < 2:
            return timedelta(0)
        diff = datetime.combine(ANY_DATE, self.times[-1]) - datetime.combine(
            ANY_DATE, self.times[0]
        )
        return diff

    @property
    def pauses(self) -> timedelta:
        if len(self.times) < 2:
            return timedelta(0)
        pauses = timedelta(seconds=0)
        for i in range(1, len(self.times) - 1, 2):
            pause = datetime.combine(ANY_DATE, self.times[i + 1]) - datetime.combine(
                ANY_DATE, self.times[i]
            )
            pauses += pause
        return pauses

    @property
    def worktime(self) -> timedelta:
        if len(self.times) < 2:
            return timedelta(0)
        worktime = self.whole_time - self.pauses
        return (
            worktime
            if worktime <= DEFAULT_WORKDAY_TIMEDELTA
            else DEFAULT_WORKDAY_TIMEDELTA
        )

    @property
    def overtime(self):
        if len(self.times) < 2:
            return timedelta(0)
        worktime = self.whole_time - self.pauses
        if worktime > DEFAULT_WORKDAY_TIMEDELTA:
            return worktime - DEFAULT_WORKDAY_TIMEDELTA
        else:
            return timedelta(seconds=0)
