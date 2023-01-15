import logging
from datetime import datetime

import pytest

from constants import WorkDay

_log = logging.getLogger(__name__)

DATE = datetime(2022, 12, 4, 0, 0)
DIFF_DATE = datetime(2022, 12, 3, 0, 0)
TIMES = [datetime(1900, 1, 1, 8, 0), datetime(1900, 1, 1, 12, 0), datetime(1900, 1, 1, 13, 0),
         datetime(1900, 1, 1, 18, 0)]
UPDATE_TIMES = [datetime(1900, 1, 1, 12, 30), datetime(1900, 1, 1, 12, 40)]
VACATION_TIMES = SICK_LEAVE_TIMES = [datetime(1900, 1, 1, 8, 0), datetime(1900, 1, 1, 16, 0)]
DAY_OFF_TIMES = []
WORKDAY = {
    "date_and_times": {
        "date": DATE,
        "times": TIMES,
    },
    "date_only": {
        "date": DATE,
    },
    "date_times_day_type": {
        "date": DATE,
        "times": VACATION_TIMES,
        "day_type": "vacation",
    },
}
UPDATE = {
    "date_and_new_time_marks": {
        "date": DATE,
        "times": UPDATE_TIMES,
    },
    "the same date, day off without time marks": {
        "date": DATE,
        "times": DAY_OFF_TIMES,
        "day_type": "day off",
    },
    "the same date, day off with time marks (wrong case)": {
        "date": DATE,
        "times": TIMES,
        "day_type": "day off",
    },
    "the same date, vacation and respective time marks": {
        "date": DATE,
        "times": VACATION_TIMES,
        "day_type": "vacation",
    },
    "the same date, vacation without time marks (wrong case)": {
        "date": DATE,
        "times": [],
        "day_type": "vacation",
    },

    "the_same_date_sick_leave_and_respective_time_marks": {
        "date": DATE,
        "times": SICK_LEAVE_TIMES,
        "day_type": "sick leave",
    },

    "without a date (wrong case)": {
        "times": [datetime(1900, 1, 1, 12, 30), datetime(1900, 1, 1, 12, 40)],
    },
    "diff date (wrong case)": {
        "date": DIFF_DATE,
        "times": [datetime(1900, 1, 1, 12, 30), datetime(1900, 1, 1, 12, 40)],
    },
}
RESULT = {
    "exist_and_new_times": [DATE, [datetime(1900, 1, 1, 8, 0), datetime(1900, 1, 1, 12, 0), datetime(1900, 1, 1, 12, 30),
                             datetime(1900, 1, 1, 12, 40), datetime(1900, 1, 1, 13, 0), datetime(1900, 1, 1, 18, 0)],
                      ""],
    "new_times": [DATE, UPDATE_TIMES, ""],
    "vacation": [DATE, VACATION_TIMES, "vacation"],
    "day_off": [DATE, DAY_OFF_TIMES, "day off"],
    "sick": [DATE, SICK_LEAVE_TIMES, "sick leave"],

}


@pytest.mark.parametrize("data", [*WORKDAY])
def test_should_create_workday_instance(data):
    assert WorkDay(data)


@pytest.mark.parametrize(
    "workday_data, update_data, result",
    [
        (WORKDAY["date_and_times"], UPDATE["date_and_new_time_marks"], RESULT["exist_and_new_times"]),
        (WORKDAY["date_and_times"], UPDATE["the same date, day off without time marks"], RESULT["day_off"]),
        (WORKDAY["date_and_times"], UPDATE["the same date, vacation and respective time marks"], RESULT["vacation"]),
        (WORKDAY["date_and_times"], UPDATE["the_same_date_sick_leave_and_respective_time_marks"], RESULT["sick"]),

        (WORKDAY["date_only"], UPDATE["date_and_new_time_marks"], RESULT["new_times"]),
        (WORKDAY["date_only"], UPDATE["the same date, day off without time marks"], RESULT["day_off"]),
        (WORKDAY["date_only"], UPDATE["the same date, vacation and respective time marks"], RESULT["vacation"]),
        (WORKDAY["date_only"], UPDATE["the_same_date_sick_leave_and_respective_time_marks"], RESULT["sick"]),
    ]
)
def test_should_update_exist_workday_instance(workday_data, update_data, result):
    workday = WorkDay(**workday_data)
    workday.update(update_data)
    assert workday.date == result[0]
    assert workday.times == result[1]
    assert workday.day_type == result[2]


@pytest.mark.parametrize(
    "workday_data, update_data, exception",
    [
        (WORKDAY["date_and_times"], {}, AssertionError),
        # covered by validating the input
        # (WORKDAY["date_and_times"], UPDATE["the same date, day off with time marks (wrong case)"], AssertionError),
    ]
)
def test_should_raise_exeption_when_wrong_update_data_passed(workday_data, update_data, exception):
    workday = WorkDay(**workday_data)
    with pytest.raises(exception) as e:
        workday.update(update_data)
        _log.info(f"ERROR: {e}")
