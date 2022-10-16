import logging
import re
from dataclasses import dataclass, field, fields
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

TABLE_COLUMNS = {"date": 120, "worktime": 100, "pause": 100, "overtime": 100, "whole time": 120, "time marks": 400}
DB_CONFIG = {"path": "/home/vova/PycharmProjects/worktime/worktime.db",
             "default_table": "worktime",
             "tables": {
                 "worktime": [
                     ("date", "VARCHAR(8) NOT NULL"),
                     ("times", "VARCHAR(200) NOT NULL"),
                 ]}}
_DEFAULT_WORKDAY_TIMEDELTA = timedelta(hours=8)
DATE_STRING_PATTERN = "%d.%m.%Y"
TIME_STRING_PATTERN = "%H:%M"
DATE_PATTERN = r"\d\d.\d\d.\d\d\d\d"
TIME_PATTERN = r"\d\d:\d\d"

_logger = logging.getLogger(__name__)


@dataclass
class WorkDay:
    date: str
    times: List[str] = field(default_factory=list)

    def __post_init__(self):
        # TODO: check values when creating WorkDay
        assert re.match(DATE_PATTERN, self.date)
        for time_mark in self.times:
            assert re.match(TIME_PATTERN, time_mark)

    def update(self, time_marks: List[str]) -> None:
        for time_mark in time_marks:
            if time_mark not in self.times:
                if re.match(TIME_PATTERN, time_mark):
                    if self._check_values(time_marks):
                        self.times.append(time_mark)
                    else:
                        _logger.error(f"Wrong time_mark passed. Skipped: {time_mark}")

    @property
    def color(self) -> str:
        if any([
            self.worktime < _DEFAULT_WORKDAY_TIMEDELTA,
            self.whole_time == timedelta(seconds=0),
        ]):
            return "red"
        elif self.overtime > timedelta(0):
            return "green"
        return "default"

    def as_tuple(self) -> Tuple:
        if self.worktime + self.pauses + self.overtime != self.whole_time:
            _logger.critical(f"Sum (worktime + pauses + overtime) != whole time")
        return str(self.date), self.worktime, self.pauses, self.overtime, self.whole_time, self.times, self.color

    def db_format(self):
        columns = [f.name for f in fields(self)]
        date_and_times = self.date, " ".join(sorted(self.times))
        return tuple(columns), date_and_times

    def as_text(self) -> str:
        times = [mark for mark in sorted(self.times)]
        result = [f'date: {self.date}\n']
        types = ["work: ", "pause: "]
        current_type = types[1]
        for i in range(len(times) - 1):
            current_type = types[1] if current_type == types[0] else types[0]
            result.extend([current_type, f"{times[i]} - {times[i + 1]}\n"])
        for name, func in zip(["worktime: ", "pauses: ", "overtime: ", "whole time: "],
                              [self.worktime, self.pauses, self.overtime, self.whole_time]):
            result.extend([name, f" {func}\n"])
        return "".join(result)

    def __str__(self):
        return f"{self.date} {' '.join(sorted(self.times))}"

    @classmethod
    def from_string(cls, data_string: str) -> Optional["WorkDay"]:
        input_elements = data_string.split()
        if not WorkDay._check_values(input_elements):
            return
        found = re.findall(rf"{DATE_PATTERN}|{TIME_PATTERN}", data_string)
        if len(found) != len(data_string.split()):
            _logger.error(f"'{data_string}' was not recognized completely: {found}")
            return
        return WorkDay(found[0], found[1:])

    @property
    def whole_time(self):
        start = datetime.strptime(self.times[-1], TIME_STRING_PATTERN)
        end = datetime.strptime(self.times[0], TIME_STRING_PATTERN)
        return start - end

    @property
    def pauses(self) -> timedelta:
        pauses = timedelta(seconds=0)
        for i in range(1, len(self.times) - 1, 2):
            time_mark = datetime.strptime(self.times[i], TIME_STRING_PATTERN)
            next_time_mark = datetime.strptime(self.times[i + 1], TIME_STRING_PATTERN)
            pause = next_time_mark - time_mark
            pauses += pause
        return pauses

    @property
    def worktime(self) -> timedelta:
        worktime = self.whole_time - self.pauses
        return worktime if worktime <= _DEFAULT_WORKDAY_TIMEDELTA else _DEFAULT_WORKDAY_TIMEDELTA

    @property
    def overtime(self):
        worktime = self.whole_time - self.pauses
        if worktime > _DEFAULT_WORKDAY_TIMEDELTA:
            return worktime - _DEFAULT_WORKDAY_TIMEDELTA
        else:
            return timedelta(seconds=0)

    @staticmethod
    def _check_values(values: List[str]) -> bool:
        if not len(values) > 1:
            _logger.error(f"Input value must include at least date and one time mark: {values}")
            return False
        for value in values:
            pattern = TIME_STRING_PATTERN if len(value) < 6 else DATE_STRING_PATTERN
            try:
                datetime.strptime(value, pattern)
            except ValueError:
                _logger.error(f"Wrong value passed: {value}")
                return False
        return True


@dataclass
class DbConfig:
    path: str
    default_table: str
    tables: Dict = field(default_factory=dict)
