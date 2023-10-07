import datetime as dt
import logging
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Union, Tuple

from dataclasses import dataclass, field

from packages.utils.utils import time_to_str

_log = logging.getLogger(__name__)

RowDictData = Dict[str, str]

MAIN_FILE_PATH = sys.modules['__main__'].__file__
assert MAIN_FILE_PATH is not None
MAIN_DIR = Path(MAIN_FILE_PATH).parent

DEFAULT_DB_PATH = f"{MAIN_DIR}/worktime.db"
CONFIG_FILE_PATH = f"{MAIN_DIR}/config.json"
LOG_FILE_PATH = f"{MAIN_DIR}/worktime.log"
DEFAULT_WORKDAY_TIMEDELTA = dt.timedelta(hours=8)
ANY_DATE = dt.date(2023, 1, 1)
DATE_STRING_MASK = "%d.%m.%Y"
TIME_STRING_MASK = "%H:%M"
DATE_PATTERN = r"\d\d.\d\d.\d\d\d\d"
ORDINAL_DATE_PATTERN = r"\d{6}"
TIME_PATTERN = r"\d\d:\d\d"
NORMAL_WORKDAY_TIMES = [
    dt.datetime.strptime("08:00", TIME_STRING_MASK).time(),
    dt.datetime.strptime("16:00", TIME_STRING_MASK).time(),
]


class DayType(Enum):
    NORMAL = ""
    VACATION = "vacation"
    HOLIDAY = "holiday"
    DAY_OFF = "day off"
    SICK = "sick"


@dataclass(frozen=True)
class DayTypeParams:
    name: DayType
    times: List[dt.time] = field(default_factory=list)


DAY_TYPE_PARAMS = [
    DayTypeParams(DayType.NORMAL, []),
    DayTypeParams(DayType.VACATION, NORMAL_WORKDAY_TIMES),
    DayTypeParams(DayType.HOLIDAY, NORMAL_WORKDAY_TIMES),
    DayTypeParams(DayType.DAY_OFF, []),
    DayTypeParams(DayType.SICK, NORMAL_WORKDAY_TIMES),
]


# TODO: Learn if class values checking after __init__ is needed
@dataclass
class WorkDay:
    date: dt.date
    times: List[dt.time] = field(default_factory=list)
    day_type: DayType = DayType.NORMAL

    @staticmethod
    def _recognize_date(value: str, mask: str) -> dt.date:
        try:
            d = dt.datetime.strptime(value, mask).date()
        except ValueError:
            try:
                d = dt.datetime.fromordinal(int(value)).date()
            except ValueError:
                _log.exception(f"Unable to recognize date. Incorrect input string: {value}")
                raise
        return d

    @classmethod
    def _find_date(cls, input_string: str) -> dt.date:
        date_values = re.findall(pattern=f"^({DATE_PATTERN}|{ORDINAL_DATE_PATTERN})", string=input_string)
        if len(date_values) != 1:
            raise ValueError(f"Input string must contain one date mark only: '{input_string}'")
        return cls._recognize_date(value=date_values[0], mask=DATE_STRING_MASK)

    @staticmethod
    def _recognize_time_marks(input_string: str) -> List[dt.time]:
        try:
            time_values = re.findall(rf" ({TIME_PATTERN})", input_string)
            times = {dt.datetime.strptime(value, TIME_STRING_MASK).time() for value in time_values}
            return list(sorted(times))
        except ValueError:
            _log.exception(f"Unable to recognize times. Incorrect input string: {input_string}")
            raise

    @staticmethod
    def _recognize_day_type(input_string: str) -> DayType:
        pattern = "|".join([item.value for item in DayType if item.value])
        day_type_values = re.findall(pattern=pattern, string=input_string)
        if not day_type_values:
            return DayType.NORMAL
        elif len(day_type_values) == 1:
            for item in DAY_TYPE_PARAMS:
                if day_type_values[0] in item.name.value:
                    return item.name
            raise AssertionError(f'Day type params not found for "{day_type_values[0]}"')
        raise ValueError(f"Input string must contain one day type only: {day_type_values}")

    @classmethod
    def from_values(cls, input_values: Union[List[str], str]) -> "WorkDay":
        string_value = input_values if isinstance(input_values, str) else " ".join(input_values)
        date_instance = cls._find_date(string_value)
        times = cls._recognize_time_marks(string_value)
        day_type = cls._recognize_day_type(string_value)
        day_type_params = [params for params in DAY_TYPE_PARAMS if params.name == day_type][0]

        if times and not day_type_params.times:
            # NORMAL (regular) day type. Input contains date and time marks
            return WorkDay(date=date_instance, times=times)
        elif not times:
            # either of VACATION, HOLIDAY, DAY_OFF, SICK day type. Input contains date and day type
            return WorkDay(date=date_instance, times=day_type_params.times, day_type=day_type_params.name)
        elif day_type_params.times and times:
            # Input contains date, day type and time marks. Check for consistency
            for item in day_type_params.times:
                if item not in times:
                    raise ValueError(
                        f'Inconsistency of input values: day type "{day_type}" '
                        f'does not match predefined time marks: {times}". '
                        f'Predefined time marks will be used.'
                    )
            return WorkDay(date=date_instance, times=day_type_params.times, day_type=day_type_params.name)
        else:
            # Invalid input value
            raise ValueError(
                f"Input must include at least one date and either time mark or day type or both: '{string_value}'"
            )

    def __add__(self, other: "WorkDay") -> "WorkDay":
        assert (
                self.date == other.date
        ), f'Only WorkDays with the same date can be added: left {self.date}, but right {other.date}'
        date_str = str(self).split()[0]
        if not other.times and not other.day_type.value:
            _log.warning(f"No new data to update: '{other}'")
            return WorkDay(self.date, self.times, self.day_type)
        if other.day_type.value:
            # new day type entered by the user
            _log.warning(
                f'For "{date_str}", time marks will be replaced in db, '
                f'because "{other.day_type.value}" day type came: '
                f'{time_to_str(self.times, TIME_STRING_MASK)} -> '
                f'{time_to_str(other.times, TIME_STRING_MASK)}'
            )
            times = sorted(list(set(other.times)))
            day_type = other.day_type
        elif self.day_type.value and not other.day_type.value:
            # no day_type entered by user, existing WorkDay will be converted to normal with new time marks
            _log.warning(
                f'For "{date_str}", time marks will be replaced in db: '
                f'{time_to_str(self.times, TIME_STRING_MASK)} -> '
                f'{time_to_str(other.times, TIME_STRING_MASK)}'
            )
            times = sorted(list(set(other.times)))
            day_type = DayType.NORMAL
        elif not self.day_type.value and not other.day_type.value:
            # both WorkDays are normal (regular)
            times_set = set(self.times)
            times_set.update(other.times)
            times = sorted(list(times_set))
            day_type = DayType.NORMAL
            _log.debug(
                f'For "{date_str}", existing time marks and new ones will be combined. '
                f'Result: {time_to_str(times, TIME_STRING_MASK)}'
            )
        else:
            _log.critical("Caught unhandled error")
            raise RuntimeError(f"Unspecified scenario between WorkDays: \n\t{self}\n\t{other}")
        return WorkDay(self.date, times, day_type)

    @property
    def color(self) -> str:
        if any([self.worktime < DEFAULT_WORKDAY_TIMEDELTA, self.whole_time == dt.timedelta(seconds=0)]):
            return "red"
        elif self.overtime > dt.timedelta(0):
            return "green"
        return "default"

    def as_dict(self) -> Dict[str, str]:
        data = dict(
            week=self.week,
            month=self.date.strftime("%B %Y"),
            date=self.date.strftime(DATE_STRING_MASK),
            weekday=str(self.date.isocalendar()[2]),
            worktime=str(self.worktime),
            pauses=str(self.pauses),
            overtime=str(self.overtime),
            whole_time=str(self.whole_time),
            time_marks=" ".join([time_mark.strftime(TIME_STRING_MASK) for time_mark in self.times]),
            color=self.color,
            day_type=self.day_type.value,
            iid=self.date.strftime(DATE_STRING_MASK),
        )
        if self.worktime + self.pauses + self.overtime != self.whole_time:
            _log.critical(f"Sum (worktime + pauses + overtime) != whole time")
        return data

    def as_db(self) -> RowDictData:
        values = {
            "date": str(self.date.toordinal()),
            "times": time_to_str(self.times, TIME_STRING_MASK),
            "day_type": self.day_type.value,
        }
        return values

    # TODO: call the function from somewhere
    def warn_if_weekend_day(self) -> None:
        if self.date.isocalendar()[2] in [6, 7]:
            _log.warning(f"The day being filled is a weekend: {self.date.strftime(DATE_STRING_MASK)}")

    def __str__(self) -> str:
        time_marks = time_to_str(self.times, TIME_STRING_MASK)
        return f'{self.date.strftime(DATE_STRING_MASK)} {time_marks} {self.day_type.value}'

    def __gt__(self, other: "WorkDay") -> bool:
        return self.date > other.date

    def __lt__(self, other: "WorkDay") -> bool:
        return self.date < other.date

    @property
    def whole_time(self) -> dt.timedelta:
        if len(self.times) < 2:
            return dt.timedelta(0)
        diff = dt.datetime.combine(ANY_DATE, self.times[-1]) - dt.datetime.combine(ANY_DATE, self.times[0])
        return diff

    @property
    def pauses(self) -> dt.timedelta:
        if len(self.times) < 2:
            return dt.timedelta(0)
        pauses = dt.timedelta(seconds=0)
        for i in range(1, len(self.times) - 1, 2):
            pause = dt.datetime.combine(ANY_DATE, self.times[i + 1]) - dt.datetime.combine(ANY_DATE, self.times[i])
            pauses += pause
        return pauses

    @property
    def worktime(self) -> dt.timedelta:
        if len(self.times) < 2:
            return dt.timedelta(0)
        worktime = self.whole_time - self.pauses
        return worktime if worktime <= DEFAULT_WORKDAY_TIMEDELTA else DEFAULT_WORKDAY_TIMEDELTA

    @property
    def overtime(self) -> dt.timedelta:
        if len(self.times) < 2:
            return dt.timedelta(0)
        worktime = self.whole_time - self.pauses
        if worktime > DEFAULT_WORKDAY_TIMEDELTA:
            return worktime - DEFAULT_WORKDAY_TIMEDELTA
        else:
            return dt.timedelta(seconds=0)

    @property
    def week(self) -> str:
        return "week " + str(self.date.isocalendar()[1]) + " " + self.date.strftime("%Y")


@dataclass(frozen=True)
class WorkWeek:
    workdays: List[WorkDay] = field(default_factory=list)
    summary_fields: Tuple[str, ...] = ("worktime", "pauses", "overtime", "whole_time")

    def __post_init__(self) -> None:
        week_first = self.workdays[0].week
        for workday in self.workdays:
            week = workday.week
            assert week == week_first, f"Week Workdays have different week number: {week_first} != {week}"

    @property
    def summary(self) -> Dict[str, str]:
        week = self.workdays[0].week
        week_summary: Dict[str, str] = dict(week=week, iid=f"summary_{week}")

        for summary_field in self.summary_fields:
            field_values = [getattr(workday, summary_field) for workday in self.workdays]
            field_sum = sum(field_values, start=dt.timedelta(0))
            hours, remainder = divmod(int(field_sum.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            result = f"{hours}h {minutes}m" if minutes else f"{hours}h"
            week_summary[summary_field] = result
        return week_summary
