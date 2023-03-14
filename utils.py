import logging
from datetime import datetime, date, time
from typing import List, Dict, Any, Union

_log = logging.getLogger(__name__)


def date_to_str(date_instance: Union[date, str], date_mask, braces: bool = False) -> str:
    try:
        if isinstance(date, str):
            date_instance = datetime.fromordinal(int(date))
        assert isinstance(date_instance, date)
        mark = date_instance.strftime(date_mask)
    except ValueError:
        mark = "<WRONG>"
    return f"[{mark}]" if braces else mark


def time_to_str(time_instances: List[time], time_mask, braces: bool = False) -> str:
    marks = [item.strftime(time_mask) for item in time_instances]
    return f'[{" ".join(marks)}]' if braces else " ".join(marks)


def dict_to_str(data: Dict[str, Any], date_mask, time_mask) -> str:
    string = ""
    for key, value in data.items():
        string += " "
        if key == "date":
            string += value.strftime(date_mask)
        elif key == "times":
            marks = [item.strftime(time_mask) for item in value]
            string += " ".join(marks)
        elif key == "day_type":
            string += value
    return string.strip()


if __name__ == "__main__":
    pass
