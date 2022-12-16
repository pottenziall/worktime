import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any

import utils

_logger = logging.getLogger(__name__)

DEFAULT_WORKDAY_TIMEDELTA = timedelta(hours=8)
DATE_STRING_MASK = "%d.%m.%Y"
TIME_STRING_MASK = "%H:%M"
DATE_PATTERN = r"\d\d.\d\d.\d\d\d\d"
ORDINAL_DATE_PATTERN = r"\d{6}"
TIME_PATTERN = r"\d\d:\d\d"
DAY_TYPE_KEYWORDS = {
    "vacation": {
        "day_type": "vacation",
        "times": [datetime.strptime("08:00", TIME_STRING_MASK), datetime.strptime("16:00", TIME_STRING_MASK)]},
    "off": {
        "day_type": "day off",
        "times": []},
    "day off": {
        "day_type": "day off",
        "times": []},
    "sick": {
        "day_type": "sick leave",
        "times": [datetime.strptime("08:00", TIME_STRING_MASK), datetime.strptime("16:00", TIME_STRING_MASK)]},
    "holiday": {
        "day_type": "holiday",
        "times": [datetime.strptime("08:00", TIME_STRING_MASK), datetime.strptime("16:00", TIME_STRING_MASK)]},
}


@dataclass
class WorkDay:
    date: datetime
    times: List[datetime] = field(default_factory=list)
    day_type: str = ""

    def update(self, data: Dict[str, Any]) -> None:
        date = utils.datetime_to_str(self.date)
        assert data.get("date", False), f'Data to update must include "date" key: {data}. WorkDay has not updated'
        assert self.date == data["date"], f'Exist WorkDay\'s can\'t be updated with data that has the different date:' \
                                          f' {data["date"]} and {self.date}. WorkDay has not updated'
        if data.get("day_type"):
            _logger.warning(
                f'For the date "{date}", time marks will be replaced in db because the new "{data["day_type"]}" day type'
                f' received: {utils.time_to_str(self.times, braces=True)} -> {utils.time_to_str(data["times"], braces=True)}')
            self.times = data["times"]
            self.day_type = data["day_type"]
        elif not data.get("day_type", False) and self.day_type:
            self.day_type = ""
            _logger.warning(f'For the date "{date}", time marks will be replaced in db: {utils.time_to_str(self.times, braces=True)} '
                            f'-> {utils.time_to_str(data["times"], braces=True)}')
            self.times = data["times"]
        elif not data.get("day_type", False) and not self.day_type:
            times = set(self.times)
            times.update(data["times"])
            self.times = sorted(list(times))
            _logger.debug(
                f'For the date "{date}", existing time marks and new ones are combined. '
                f'Result: {utils.time_to_str(self.times, braces=True)}')
        else:
            _logger.critical("Caught unhandled error")

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
        data = dict(week=str(self.date.isocalendar()[1]),
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
            _logger.critical(f"Sum (worktime + pauses + overtime) != whole time")
        return data

    def __str__(self):
        time_marks = utils.time_to_str(self.times)
        return f'{self.date.strftime(DATE_STRING_MASK)} {time_marks} {self.day_type if self.day_type else ""}'

    @property
    def whole_time(self) -> timedelta:
        if len(self.times) < 2:
            return timedelta(0)
        return self.times[-1] - self.times[0]

    @property
    def pauses(self) -> timedelta:
        if len(self.times) < 2:
            return timedelta(0)
        pauses = timedelta(seconds=0)
        for i in range(1, len(self.times) - 1, 2):
            pause = self.times[i + 1] - self.times[i]
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
