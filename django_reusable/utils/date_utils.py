import operator
from datetime import datetime, timedelta, date

from .utils import get_offset_range

# Mapping of months to their respective quarters
QUARTER_MAP = {}
QUARTER_MAP.update(dict(zip((1, 2, 3), ('Q1',) * 3)))
QUARTER_MAP.update(dict(zip((4, 5, 6), ('Q2',) * 3)))
QUARTER_MAP.update(dict(zip((7, 8, 9), ('Q3',) * 3)))
QUARTER_MAP.update(dict(zip((10, 11, 12), ('Q4',) * 3)))

# Abbreviated month names
MONTH_NAMES_ABBREV = [('01', 'Jan'),
                      ('02', 'Feb'),
                      ('03', 'Mar'),
                      ('04', 'Apr'),
                      ('05', 'May'),
                      ('06', 'Jun'),
                      ('07', 'Jul'),
                      ('08', 'Aug'),
                      ('09', 'Sep'),
                      ('10', 'Oct'),
                      ('11', 'Nov'),
                      ('12', 'Dec')]

# Full month names
MONTH_NAMES = [('01', 'January'),
               ('02', 'February'),
               ('03', 'March'),
               ('04', 'April'),
               ('05', 'May'),
               ('06', 'June'),
               ('07', 'July'),
               ('08', 'August'),
               ('09', 'September'),
               ('10', 'October'),
               ('11', 'November'),
               ('12', 'December')]

# Dictionaries for month names
MONTH_NAMES_DICT = dict(MONTH_NAMES)
MONTH_NAMES_ABBREV_DICT = dict(MONTH_NAMES_ABBREV)
MONTH_INT_NAMES_DICT = dict((int(k), v) for (k, v) in MONTH_NAMES)
MONTH_NAMES_ABBREV_INT_DICT = dict((int(k), v) for (k, v) in MONTH_NAMES_ABBREV)


def get_month_label(month, abbrev=False):
    """
    Retrieves the month label.

    Args:
        month (int): The month number.
        abbrev (bool): Whether to return the abbreviated month name.

    Returns:
        str: The month label.
    """
    return MONTH_NAMES_ABBREV_INT_DICT[int(month)] if abbrev else MONTH_INT_NAMES_DICT[int(month)]


def get_year_month_label(year, month, abbrev=False):
    """
    Retrieves the year and month label.

    Args:
        year (int): The year.
        month (int): The month number.
        abbrev (bool): Whether to return the abbreviated month name.

    Returns:
        str: The year and month label.
    """
    return f'{get_month_label(month, abbrev)} {year}'


def get_current_quarter():
    """
    Retrieves the current quarter and its months.

    Returns:
        tuple: The current quarter and a list of its months.
    """
    current_quarter = QUARTER_MAP[datetime.now().month]
    return current_quarter, list((k for (k, v) in QUARTER_MAP.items() if v == current_quarter))


def get_quarter(quarter_number):
    """
    Retrieves the quarter and its months.

    Args:
        quarter_number (int): The quarter number.

    Returns:
        tuple: The quarter and a list of its months.
    """
    quarter = 'Q%s' % quarter_number
    return quarter, list((k for (k, v) in QUARTER_MAP.items() if v == quarter))


def get_adj_months(ref_day, offset):
    """
    Retrieves the adjusted months based on the reference day and offset.

    Args:
        ref_day (datetime): The reference day.
        offset (int): The number of months to adjust.

    Returns:
        list: A list of tuples containing the adjusted month and year.
    """
    result = []
    current = ref_day
    is_negative = offset < 0
    for x in range(0, abs(offset)):
        adj_month = current.replace(day=1 if is_negative else 28) + timedelta(days=-1 if is_negative else 4)
        result.append((adj_month.month, adj_month.year))
        current = adj_month
    if is_negative:
        result.reverse()
    return result


def get_adjacent_months(month, year, plus=0, minus=0):
    """
    Retrieves the adjacent months based on the given month, year, and offsets.

    Args:
        month (int): The month number.
        year (int): The year.
        plus (int): The number of months to add.
        minus (int): The number of months to subtract.

    Returns:
        list: A list of tuples containing the adjacent months and years.
    """
    day = datetime(year, month, 1)
    return get_adj_months(day, minus * -1) + [(day.month, day.year)] + get_adj_months(day, plus)


def is_first_day_of_month(date_to_check=None):
    """
    Checks if the given date is the first day of the month.

    Args:
        date_to_check (datetime, optional): The date to check. Defaults to today.

    Returns:
        bool: True if the date is the first day of the month, False otherwise.
    """
    date_to_check = date_to_check or datetime.today()
    return date_to_check.month != (date_to_check - timedelta(days=1)).month


def is_last_day_of_month(date_to_check=None):
    """
    Checks if the given date is the last day of the month.

    Args:
        date_to_check (datetime, optional): The date to check. Defaults to today.

    Returns:
        bool: True if the date is the last day of the month, False otherwise.
    """
    date_to_check = date_to_check or datetime.today()
    return date_to_check.month != (date_to_check + timedelta(days=1)).month


def is_last_day_of_quarter(date_to_check=None):
    """
    Checks if the given date is the last day of the quarter.

    Args:
        date_to_check (datetime, optional): The date to check. Defaults to today.

    Returns:
        bool: True if the date is the last day of the quarter, False otherwise.
    """
    date_to_check = date_to_check or datetime.today()
    return (QUARTER_MAP[date_to_check.month] !=
            QUARTER_MAP[(date_to_check + timedelta(days=1)).month])


def first_day_of_month(year: int, month: int):
    """
    Retrieves the first day of the given month and year.

    Args:
        year (int): The year.
        month (int): The month number.

    Returns:
        datetime: The first day of the month.
    """
    return datetime(year, month, 1)


def get_last_month():
    """
    Retrieves the last month and its year.

    Returns:
        tuple: The last month and its year.
    """
    first_day = datetime(datetime.today().year, datetime.today().month, 1)
    last_day_of_last_month = first_day - timedelta(days=1)
    return last_day_of_last_month.month, last_day_of_last_month.year


def last_day_of_month(day: date = None, year: int = None, month: int = None):
    """
    Retrieves the last day of the given month and year.

    Args:
        day (date, optional): The reference day.
        year (int, optional): The year.
        month (int, optional): The month number.

    Returns:
        datetime: The last day of the month.

    Raises:
        Exception: If neither day nor (year, month) are provided.
    """
    if not day and year and month:
        day = datetime(year, month, 1, 23, 59, 59)
    if not day:
        raise Exception("Please pass 'day' or (year, month)")
    next_month = day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def get_adj_month_first_day(day: date, for_next=True):
    """
    Retrieves the first day of the adjacent month.

    Args:
        day (date): The reference day.
        for_next (bool): Whether to get the next month's first day.

    Returns:
        datetime: The first day of the adjacent month.
    """
    if for_next:
        return last_day_of_month(day) + timedelta(days=1)
    else:
        return (day.replace(day=1) - timedelta(days=1)).replace(day=1)


def next_weekday(d, weekday):
    """
    Retrieves the next specified weekday after the given date.

    Args:
        d (datetime): The reference date.
        weekday (int): The target weekday (0=Monday, 6=Sunday).

    Returns:
        datetime: The next specified weekday.
    """
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def get_adjacent_dates(ref_date=None, plus=0, minus=0):
    """
    Retrieves the adjacent dates based on the reference date and offsets.

    Args:
        ref_date (datetime, optional): The reference date. Defaults to today.
        plus (int): The number of days to add.
        minus (int): The number of days to subtract.

    Returns:
        list: A list of adjacent dates.
    """
    day_range = get_offset_range(minus, plus)
    day = ref_date or datetime.today()
    return [day + timedelta(days=offset) for offset in day_range]


def is_date(_input: str, _format: str):
    """
    Checks if the given input is a valid date in the specified format.

    Args:
        _input (str): The input string.
        _format (str): The date format.

    Returns:
        bool: True if the input is a valid date, False otherwise.
    """
    try:
        return bool(datetime.strptime(_input, _format))
    except ValueError:
        return False
