import logging
from datetime import date, time
from typing import List

import pytest

from packages.constants import WorkDay, DayType, WorkWeek

_log = logging.getLogger(__name__)

DATE_1 = date(2023, 9, 11)
DATE_2 = date(2023, 9, 12)
DATE_3 = date(2023, 9, 13)
DATE_4 = date(2023, 9, 14)
DATE_5 = date(2023, 9, 15)
DATE_6 = date(2023, 9, 18)
TIMES_1 = [time(8), time(12), time(13), time(18)]
TIMES_2 = [time(8), time(16)]

WORKDAYS_THE_SAME_WEEK = [
    WorkDay(date=DATE_1, times=TIMES_1),
    WorkDay(date=DATE_2, times=TIMES_2, day_type=DayType.VACATION),
    WorkDay(date=DATE_3),
    WorkDay(date=DATE_4, times=TIMES_1),
    WorkDay(date=DATE_5, times=TIMES_1),
]
WORKDAYS_DIFFERENT_WEEKS = [WorkDay(date=DATE_3), WorkDay(date=DATE_6, times=TIMES_1)]


class TestWorkWeek:
    @pytest.mark.parametrize("workdays", [WORKDAYS_THE_SAME_WEEK])
    def test_should_print_summary_properly(self, workdays: List[WorkDay]) -> None:
        workweek = WorkWeek(workdays)
        assert workweek.workdays == workdays
        assert workweek.summary == {
            'iid': 'summary_week 37 2023',
            'overtime': '3h',
            'pauses': '3h',
            'week': 'week 37 2023',
            'whole_time': '38h',
            'worktime': '32h',
        }

    @pytest.mark.parametrize("workdays", [WORKDAYS_DIFFERENT_WEEKS])
    def test_should_raise_assertion_error_when_workdays_from_different_weeks(self, workdays: List[WorkDay]) -> None:
        with pytest.raises(AssertionError):
            WorkWeek(workdays)
