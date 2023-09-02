import datetime as dt
import logging
from typing import List, Union

_log = logging.getLogger(__name__)


def date_to_str(date_instance: Union[dt.date, str], date_mask, braces: bool = False) -> str:
    try:
        if isinstance(date_instance, str):
            date_instance = dt.datetime.fromordinal(int(date_instance))
        assert isinstance(date_instance, dt.date)
        mark = date_instance.strftime(date_mask)
    except ValueError:
        mark = "<WRONG>"
    return f"[{mark}]" if braces else mark


def time_to_str(time_instances: List[dt.time], time_mask, braces: bool = False) -> str:
    marks = [item.strftime(time_mask) for item in time_instances]
    return f'[{" ".join(marks)}]' if braces else " ".join(marks)


if __name__ == "__main__":
    pass
