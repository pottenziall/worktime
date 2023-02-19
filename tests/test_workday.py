import logging
from datetime import datetime, timedelta, date, time
from typing import Any, Dict, List

import pytest  # type: ignore

from constants import WorkDay

_log = logging.getLogger(__name__)

DATE_1 = date(2022, 12, 4)
DATE_2 = date(2022, 12, 3)
TIMES_1 = [time(8), time(12), time(13), time(18)]
TIMES_2 = [time(12, 30), time(12, 40)]
TIMES_3 = [time(13), time(14)]
TIMES_4 = [time(18), time(18)]
TIMES_5 = [time(8), time(16)]
TIMES = {
    "vacation": [time(8), time(16)],
    "sick leave": [time(8), time(16)],
    "day off": [],
}
INPUT_VALUES = {
    "04.12.2022 vacation": [DATE_1, TIMES_5, "vacation"],
    "04.12.2022  08:00 12:00 13:00 18:00": [DATE_1, TIMES_1, ""],
    "04.12.2022 08:00 12:00 13:00 18:00": [DATE_1, TIMES_1, ""],
    "04.12.2022 18:00 18:00": [DATE_1, [time(18)], ""],
}
WRONG_INPUT_VALUES = [
    "08:00",
    "04.12.2022",
    "34.12.2022 08:00",
    "04.12.2022 28:00",
]

WORKDAY_WITH_DATE_AND_TIMES = {
    "date": DATE_1,
    "times": TIMES_1,
}
WORKDAY_WITH_DATE_ONLY = {
    "date": DATE_1,
}
WORKDAY_DATE_AND_TIMES_AND_VACATION = {
    "date": DATE_1,
    "times": TIMES["vacation"],
    "day_type": "vacation",
}
WORKDAYS_WRONG_DATA = [
    {"date": "04.12.2022", "times": ["25:00"]},
    {"date": "34.12.2022", "times": ["08:00"]},
]
WORKDAYS_DATA = [
    WORKDAY_WITH_DATE_AND_TIMES,
    WORKDAY_WITH_DATE_ONLY,
    WORKDAY_DATE_AND_TIMES_AND_VACATION,
]

UPDATE_DATE_ONLY = {
    "date": DATE_1,
    "times": [],
}
UPDATE_NEW_TIME_MARKS = {
    "date": DATE_1,
    "times": TIMES_2,
}
UPDATE_INCLUDE_SAME_TIME_MARK = {
    "date": DATE_1,
    "times": TIMES_3,
}
UPDATE_TWO_EQUAL_TIME_MARKS = {
    "date": DATE_1,
    "times": TIMES_4,
}
UPDATE_DAY_OFF_WITH_RESPECTIVE_TIME_MARKS = {
    "date": DATE_1,
    "times": TIMES["day off"],
    "day_type": "day off",
}
UPDATE_DAY_OFF_WITH_TIME_MARKS_WRONG_CASE = {
    "date": DATE_1,
    "times": TIMES_1,
    "day_type": "day off",
}
UPDATE_VACATION_WITH_RESPECTIVE_TIME_MARKS = {
    "date": DATE_1,
    "times": TIMES["vacation"],
    "day_type": "vacation",
}
UPDATE_VACATION_WITH_WRONG_TIME_MARKS_WRONG_CASE = {
    "date": DATE_1,
    "times": [],
    "day_type": "vacation",
}
UPDATE_SICK_LEAVE_WITH_RESPECTIVE_TIME_MARKS = {
    "date": DATE_1,
    "times": TIMES["sick leave"],
    "day_type": "sick leave",
}
UPDATE_WITHOUT_DATE_WRONG_CASE = {
    "times": [datetime(1900, 1, 1, 12, 30), datetime(1900, 1, 1, 12, 40)],
}
UPDATE_WITH_DIFF_DATE_WRONG_CASE = {
    "date": DATE_2,
    "times": [datetime(1900, 1, 1, 12, 30), datetime(1900, 1, 1, 12, 40)],
}
UPDATE_DATA = [
    UPDATE_NEW_TIME_MARKS,
    UPDATE_DAY_OFF_WITH_RESPECTIVE_TIME_MARKS,
    UPDATE_VACATION_WITH_RESPECTIVE_TIME_MARKS,
    UPDATE_SICK_LEAVE_WITH_RESPECTIVE_TIME_MARKS,
    UPDATE_INCLUDE_SAME_TIME_MARK,
    UPDATE_TWO_EQUAL_TIME_MARKS,
    UPDATE_DATE_ONLY,
]
WRONG_UPDATE_DATA = [UPDATE_WITHOUT_DATE_WRONG_CASE, UPDATE_WITH_DIFF_DATE_WRONG_CASE]


@pytest.fixture(scope="function", params=INPUT_VALUES.items())
def input_values(request) -> Dict[str, List[Any]]:
    return request.param


@pytest.fixture(scope="function", params=WRONG_INPUT_VALUES)
def wrong_input_values(request) -> str:
    return request.param


@pytest.fixture(scope="function", params=WORKDAYS_DATA)
def workday_data(request) -> Dict[str, Any]:
    return request.param


@pytest.fixture(scope="function", params=WORKDAYS_WRONG_DATA)
def wrong_workday_data(request) -> Dict[str, Any]:
    return request.param


@pytest.fixture(scope="function", params=UPDATE_DATA)
def update_data(request) -> Dict[str, Any]:
    return request.param


@pytest.fixture(scope="function", params=WRONG_UPDATE_DATA)
def wrong_update_data(request) -> Dict[str, Any]:
    return request.param


class TestCreateWorkday:
    def test_should_create_workday_from_values(
            self, workday_data: Dict[str, Any]
    ) -> None:
        w = WorkDay(**workday_data)
        assert w.date == workday_data["date"]
        assert w.times == workday_data.get("times", [])
        assert w.day_type == workday_data.get("day_type", "")

    # Use for testing the function which creates workday
    # def test_should_raise_value_error_when_wrong_input_values(self, wrong_workday_data: Dict[str, Any]) -> None:
    #    with pytest.raises(ValueError):
    #        WorkDay(**wrong_workday_data)

    def test_should_create_workday_from_string(
            self, input_values: Dict[str, List[Any]]
    ) -> None:
        input_string, (date, times, day_type) = input_values
        w = WorkDay.from_values(input_string)
        assert w.date == date
        assert w.times == times
        assert w.day_type == day_type

    def test_should_raise_value_error_when_wrong_input_string(
            self, wrong_input_values: str
    ) -> None:
        with pytest.raises(ValueError):
            WorkDay.from_values(wrong_input_values)


class TestUpdateWorkday:
    def test_should_update_workday_instance(
            self, workday_data: Dict[str, Any], update_data: Dict[str, Any]
    ) -> None:
        workday = WorkDay(**workday_data)
        workday.update(update_data)
        day_type = update_data.get("day_type", "")
        if day_type or workday_data.get("day_type", ""):
            assert workday.times == update_data.get("times")
            assert workday.day_type == day_type
        else:
            times = set(workday_data.get("times", []) + update_data.get("times"))
            assert workday.times == sorted(list(times))

    def test_should_raise_assertion_error_when_wrong_update_data_passed(
            self, workday_data: Dict[str, Any], wrong_update_data: Dict[str, Any]
    ) -> None:
        workday = WorkDay(**workday_data)
        with pytest.raises(AssertionError):
            workday.update(wrong_update_data)


@pytest.mark.parametrize(
    "date_ins, times, day_type, results",
    [
        (
                date(2023, 2, 9),
                [],
                "",
                {
                    "week": "week 6",
                    "month": "February 2023",
                    "date": "09.02.2023",
                    "weekday": 4,
                    "worktime": timedelta(hours=0),
                    "pause": timedelta(hours=0),
                    "overtime": timedelta(hours=0),
                    "whole_time": timedelta(hours=0),
                    "time_marks": [],
                    "color": "red",
                    "day_type": "",
                },
        ),
        (
                date(2023, 1, 1),
                [time(8), time(12), time(13), time(18)],
                "",
                {
                    "week": "week 52",
                    "month": "January 2023",
                    "date": "01.01.2023",
                    "weekday": 7,
                    "worktime": timedelta(hours=8),
                    "pause": timedelta(hours=1),
                    "overtime": timedelta(hours=1),
                    "whole_time": timedelta(hours=10),
                    "time_marks": ["08:00", "12:00", "13:00", "18:00"],
                    "color": "green",
                    "day_type": "",
                },
        ),
        (
                date(2023, 1, 5),
                [time(8), time(16)],
                "vacation",
                {
                    "week": "week 1",
                    "month": "January 2023",
                    "date": "05.01.2023",
                    "weekday": 4,
                    "worktime": timedelta(hours=8),
                    "pause": timedelta(hours=0),
                    "overtime": timedelta(hours=0),
                    "whole_time": timedelta(hours=8),
                    "time_marks": ["08:00", "16:00"],
                    "color": "default",
                    "day_type": "vacation",
                },
        ),
    ],
)
def test_should_save_values_as_dict(
        date_ins: date, times: List[time], day_type: str, results: Dict[str, Any]
) -> None:
    workday = WorkDay(date=date_ins, times=times, day_type=day_type)
    dict_values = workday.as_dict()
    assert len(dict_values) == 11
    for k, v in dict_values.items():
        assert results[k] == v
