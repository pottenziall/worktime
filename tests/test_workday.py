import logging
from datetime import datetime, timedelta, date, time
from typing import Any, Dict, List

import pytest

from constants import WorkDay, DayType

_log = logging.getLogger(__name__)

DATE_1 = date(2022, 12, 4)
DATE_2 = date(2022, 12, 3)
TIMES_1 = [time(8), time(12), time(13), time(18)]
TIMES_2 = [time(12, 30), time(12, 40)]
TIMES_3 = [time(13), time(14)]
TIMES_4 = [time(18), time(18)]
TIMES_5 = [time(8), time(16)]
TIMES = {"vacation": [time(8), time(16)], "sick leave": [time(8), time(16)], "day off": []}

WORKDAY_WITH_DATE_AND_TIMES = {"date": DATE_1, "times": TIMES_1}
WORKDAY_WITH_DATE_ONLY = {"date": DATE_1}
WORKDAY_DATE_AND_TIMES_AND_VACATION = {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION}
WORKDAYS_WRONG_DATA = [{"date": "04.12.2022", "times": ["25:00"]}, {"date": "34.12.2022", "times": ["08:00"]}]
WORKDAYS_DATA = [WORKDAY_WITH_DATE_AND_TIMES, WORKDAY_WITH_DATE_ONLY, WORKDAY_DATE_AND_TIMES_AND_VACATION]

UPDATE_DATE_ONLY = {"date": DATE_1, "times": []}
UPDATE_NEW_TIME_MARKS = {"date": DATE_1, "times": TIMES_2}
UPDATE_INCLUDE_SAME_TIME_MARK = {"date": DATE_1, "times": TIMES_3}
UPDATE_TWO_EQUAL_TIME_MARKS = {"date": DATE_1, "times": TIMES_4}
UPDATE_DAY_OFF_WITH_RESPECTIVE_TIME_MARKS = {"date": DATE_1, "times": TIMES["day off"], "day_type": DayType.DAY_OFF}
UPDATE_DAY_OFF_WITH_TIME_MARKS_WRONG_CASE = {"date": DATE_1, "times": TIMES_1, "day_type": DayType.DAY_OFF}
UPDATE_VACATION_WITH_RESPECTIVE_TIME_MARKS = {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION}
UPDATE_VACATION_WITH_WRONG_TIME_MARKS_WRONG_CASE = {"date": DATE_1, "times": [], "day_type": DayType.VACATION}
UPDATE_SICK_LEAVE_WITH_RESPECTIVE_TIME_MARKS = {"date": DATE_1, "times": TIMES["sick leave"], "day_type": DayType.SICK}
UPDATE_WITHOUT_DATE_WRONG_CASE = {"times": [datetime(1900, 1, 1, 12, 30), datetime(1900, 1, 1, 12, 40)]}
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


class TestCreateWorkday:
    @pytest.mark.parametrize(
        "workday_values",
        [
            {"date": DATE_1},
            {"date": DATE_1, "times": TIMES_1},
            {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION},
        ],
    )
    def test_should_create_workday_from_values(self, workday_values: Dict[str, Any]) -> None:
        w = WorkDay(**workday_values)
        assert w.date == workday_values["date"]
        assert w.times == workday_values.get("times", [])
        assert w.day_type == workday_values.get("day_type", DayType.NORMAL)

    @pytest.mark.parametrize(
        "input_string, date_ins, times, day_type",
        [
            ("04.12.2022 vacation", DATE_1, TIMES_5, DayType.VACATION),
            ("04.12.2022  08:00 12:00 13:00 18:00", DATE_1, TIMES_1, DayType.NORMAL),
            ("04.12.2022 08:00 12:00 13:00 18:00", DATE_1, TIMES_1, DayType.NORMAL),
            ("04.12.2022 18:00 18:00", DATE_1, [time(18)], DayType.NORMAL),
        ],
    )
    def test_should_create_workday_from_string(
        self, input_string: str, date_ins: date, times: List[time], day_type: DayType
    ) -> None:
        w = WorkDay.from_values(input_string)
        assert w.date == date_ins
        assert w.times == times
        assert w.day_type == day_type

    @pytest.mark.parametrize(
        "input_string", ["08:00", "34.12.2022 08:00", "04.12.2022 28:00", "04.12.2022 08:00 vacation"]
    )
    def test_should_raise_value_error_when_wrong_input_string(self, input_string: str) -> None:
        with pytest.raises(ValueError):
            WorkDay.from_values(input_string)


class TestAddWorkdays:
    @pytest.mark.parametrize(
        "workday_values, update_values",
        [
            ({"date": DATE_1, "times": TIMES_1}, {"date": DATE_1, "times": []}),
            ({"date": DATE_1, "times": TIMES_1}, {"date": DATE_1}),
            ({"date": DATE_1}, {"date": DATE_1, "times": []}),
            ({"date": DATE_1}, {"date": DATE_1}),
            ({"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION}, {"date": DATE_1, "times": []}),
            ({"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION}, {"date": DATE_1}),
        ],
    )
    def test_should_keep_workday_values_without_change(
            self, workday_values: Dict[str, Any], update_values: Dict[str, Any]
    ) -> None:
        first_workday = WorkDay(**workday_values)
        second_workday = WorkDay(**update_values)
        third_workday = first_workday + second_workday
        assert third_workday.times == first_workday.times
        assert third_workday.day_type == first_workday.day_type

    @pytest.mark.parametrize(
        "workday_values, update_values",
        [
            ({"date": DATE_1}, {"date": DATE_1, "times": TIMES_4}),
            ({"date": DATE_1}, {"date": DATE_1, "times": TIMES["day off"], "day_type": DayType.DAY_OFF}),
            ({"date": DATE_1}, {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION}),
            ({"date": DATE_1}, {"date": DATE_1, "times": TIMES["sick leave"], "day_type": DayType.SICK}),
            ({"date": DATE_1, "times": TIMES_1}, {"date": DATE_1, "times": TIMES_1}),
            (
                {"date": DATE_1, "times": TIMES_1},
                {"date": DATE_1, "times": TIMES["day off"], "day_type": DayType.DAY_OFF},
            ),
            (
                {"date": DATE_1, "times": TIMES_1},
                {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION},
            ),
            (
                {"date": DATE_1, "times": TIMES_1},
                {"date": DATE_1, "times": TIMES["sick leave"], "day_type": DayType.SICK},
            ),
            (
                {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION},
                {"date": DATE_1, "times": TIMES_4},
            ),
            (
                {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION},
                {"date": DATE_1, "times": TIMES["day off"], "day_type": DayType.DAY_OFF},
            ),
            (
                {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION},
                {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION},
            ),
            (
                {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION},
                {"date": DATE_1, "times": TIMES["sick leave"], "day_type": DayType.SICK},
            ),
        ],
    )
    def test_should_replace_first_workday_values_with_values_from_second_workday(
        self, workday_values: Dict[str, Any], update_values: Dict[str, Any]
    ) -> None:
        first_workday = WorkDay(**workday_values)
        second_workday = WorkDay(**update_values)
        third_workday = first_workday + second_workday
        assert third_workday.times == sorted(list(set(second_workday.times)))
        assert third_workday.day_type == second_workday.day_type

    @pytest.mark.parametrize(
        "workday_values, update_values",
        [
            ({"date": DATE_1, "times": TIMES_1}, {"date": DATE_1, "times": TIMES_2}),
            ({"date": DATE_1, "times": TIMES_1}, {"date": DATE_1, "times": TIMES_1}),
            ({"date": DATE_1, "times": TIMES_1}, {"date": DATE_1, "times": TIMES_4}),
            ({"date": DATE_1}, {"date": DATE_1, "times": TIMES_2}),
            ({"date": DATE_1}, {"date": DATE_1, "times": TIMES_4}),
        ],
    )
    def test_should_combine_values_from_both_workdays(
        self, workday_values: Dict[str, Any], update_values: Dict[str, Any]
    ) -> None:
        first_workday = WorkDay(**workday_values)
        second_workday = WorkDay(**update_values)
        third_workday = first_workday + second_workday
        times = set(first_workday.times + second_workday.times)
        assert third_workday.times == sorted(list(times))
        assert third_workday.day_type == first_workday.day_type

    @pytest.mark.parametrize(
        "workday_values, update_values", [({"date": DATE_1, "times": TIMES_1}, {"date": DATE_2, "times": TIMES_4})]
    )
    def test_should_raise_assertion_error_when_workdays_dates_differ(
        self, workday_values: Dict[str, Any], update_values: Dict[str, Any]
    ) -> None:
        first_workday = WorkDay(**workday_values)
        second_workday = WorkDay(**update_values)
        with pytest.raises(AssertionError):
            first_workday + second_workday


class TestConvertWorkday:
    @pytest.mark.parametrize(
        "date_ins, times, day_type, results",
        [
            (
                date(2023, 2, 9),
                [],
                DayType.NORMAL,
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
                    "day_type": DayType.NORMAL.value,
                },
            ),
            (
                date(2023, 1, 1),
                [time(8), time(12), time(13), time(18)],
                DayType.NORMAL,
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
                    "day_type": DayType.NORMAL.value,
                },
            ),
            (
                date(2023, 1, 5),
                [time(8), time(16)],
                DayType.VACATION,
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
                    "day_type": DayType.VACATION.value,
                },
            ),
        ],
    )
    def test_should_save_workday_as_dict(
        self, date_ins: date, times: List[time], day_type: DayType, results: Dict[str, Any]
    ) -> None:
        workday = WorkDay(date=date_ins, times=times, day_type=day_type)
        dict_values = workday.as_dict()
        assert len(dict_values) == 11
        for k, v in dict_values.items():
            assert results[k] == v

    @pytest.mark.parametrize(
        "workday_values, result",
        [
            (
                {"date": DATE_1, "times": TIMES_1},
                {'date': '738493', 'day_type': '', 'times': '08:00 12:00 13:00 18:00'},
            ),
            ({"date": DATE_1}, {'date': '738493', 'day_type': '', 'times': ''}),
        ],
    )
    def test_should_prepare_workday_for_db(self, workday_values: Dict[str, Any], result: Dict[str, Any]) -> None:
        values_for_db = WorkDay(**workday_values).as_db()
        assert values_for_db == result

    @pytest.mark.parametrize(
        "workday_values, result",
        [
            ({"date": DATE_1, "times": TIMES_1}, "04.12.2022 08:00 12:00 13:00 18:00 "),
            (
                {"date": DATE_1, "times": TIMES["vacation"], "day_type": DayType.VACATION},
                "04.12.2022 08:00 16:00 vacation",
            ),
        ],
    )
    def test_should_print_workday_properly(self, workday_values: Dict[str, Any], result: Dict[str, Any]) -> None:
        workday = WorkDay(**workday_values)
        assert str(workday) == result

    # TODO:
    # test_should_warn_if_weekend_day
    # test_should_return_proper_color_name
