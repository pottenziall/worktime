from datetime import datetime
from typing import List, Dict, Any, Union

import constants
from models import Worktime


def datetime_to_str(date: Union[datetime, str], braces: bool = False) -> str:
    try:
        if isinstance(date, str):
            date = datetime.fromordinal(int(date))
        mark = date.strftime(constants.DATE_STRING_MASK)
    except ValueError:
        mark = "<WRONG>"
    return f'[{mark}]' if braces else mark


def time_to_str(data: List[datetime], braces: bool = False) -> str:
    marks = [item.strftime(constants.TIME_STRING_MASK) for item in data]
    return f'[{" ".join(marks)}]' if braces else " ".join(marks)


def dict_to_str(data: Dict[str, Any]) -> str:
    string = ""
    for key, value in data.items():
        string += " "
        if key == "date":
            string += value.strftime(constants.DATE_STRING_MASK)
        elif key == "times":
            marks = [item.strftime(constants.TIME_STRING_MASK) for item in value]
            string += " ".join(marks)
        elif key == "day_type":
            string += value
    return string.strip()


def get_query_result_values(result: List[Worktime]) -> List[Any]:
    columns = result[0].__table__.columns.keys() if result else []
    return [[str(row.__getattribute__(c)) for c in columns] for row in result]


if __name__ == '__main__':
    res = dict_to_str(
        {"date": datetime(1900, 1, 1, 8, 0),
         "times": [datetime(1900, 1, 1, 12, 30), datetime(1900, 1, 1, 12, 40)],
         "day_type": "vacation"
         }
    )
    print(res)
