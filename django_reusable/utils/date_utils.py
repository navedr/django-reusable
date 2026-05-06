import operator
from datetime import datetime, timedelta, date

from .utils import get_offset_range

QUARTER_MAP = {}
"""dict: Maps month numbers (1-12) to quarter labels (Q1-Q4)."""
QUARTER_MAP.update(dict(zip((1, 2, 3), ('Q1',) * 3)))
QUARTER_MAP.update(dict(zip((4, 5, 6), ('Q2',) * 3)))
QUARTER_MAP.update(dict(zip((7, 8, 9), ('Q3',) * 3)))
QUARTER_MAP.update(dict(zip((10, 11, 12), ('Q4',) * 3)))

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
"""list[tuple[str, str]]: Zero-padded month number to abbreviated name pairs."""

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
"""list[tuple[str, str]]: Zero-padded month number to full name pairs."""

MONTH_NAMES_DICT = dict(MONTH_NAMES)
MONTH_NAMES_ABBREV_DICT = dict(MONTH_NAMES_ABBREV)
MONTH_INT_NAMES_DICT = dict((int(k), v) for (k, v) in MONTH_NAMES)
MONTH_NAMES_ABBREV_INT_DICT = dict((int(k), v) for (k, v) in MONTH_NAMES_ABBREV)


def get_month_label(month, abbrev=False):
    """Return the name of a month by its number.

    Args:
        month: Month number (1-12), as int or string.
        abbrev: If True, return abbreviated name (e.g. ``'Jan'``).

    Returns:
        str: Month name.
    """
    return MONTH_NAMES_ABBREV_INT_DICT[int(month)] if abbrev else MONTH_INT_NAMES_DICT[int(month)]


def get_year_month_label(year, month, abbrev=False):
    """Return a formatted ``'Month Year'`` label.

    Args:
        year: Year number.
        month: Month number (1-12).
        abbrev: If True, use abbreviated month name.

    Returns:
        str: Label like ``'January 2024'`` or ``'Jan 2024'``.
    """
    return f'{get_month_label(month, abbrev)} {year}'


def get_current_quarter():
    """Return the current calendar quarter and its months.

    Returns:
        tuple[str, list[int]]: Quarter label (e.g. ``'Q1'``) and list of month numbers.
    """
    current_quarter = QUARTER_MAP[datetime.now().month]
    return current_quarter, list((k for (k, v) in QUARTER_MAP.items() if v == current_quarter))


def get_quarter(quarter_number):
    """Return a quarter label and its months by quarter number.

    Args:
        quarter_number: Quarter number (1-4).

    Returns:
        tuple[str, list[int]]: Quarter label (e.g. ``'Q2'``) and list of month numbers.
    """
    quarter = 'Q%s' % quarter_number
    return quarter, list((k for (k, v) in QUARTER_MAP.items() if v == quarter))


def get_adj_months(ref_day, offset):
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
    """Return a list of (month, year) tuples around a reference month.

    Args:
        month: Reference month number.
        year: Reference year.
        plus: Number of months after the reference to include.
        minus: Number of months before the reference to include.

    Returns:
        list[tuple[int, int]]: (month, year) tuples in chronological order.
    """
    day = datetime(year, month, 1)
    return get_adj_months(day, minus * -1) + [(day.month, day.year)] + get_adj_months(day, plus)


def is_first_day_of_month(date_to_check=None):
    """Check if a date is the first day of its month.

    Args:
        date_to_check: Date to check. Defaults to today.

    Returns:
        bool: True if it is the first day.
    """
    date_to_check = date_to_check or datetime.today()
    return date_to_check.month != (date_to_check - timedelta(days=1)).month


def is_last_day_of_month(date_to_check=None):
    """Check if a date is the last day of its month.

    Args:
        date_to_check: Date to check. Defaults to today.

    Returns:
        bool: True if it is the last day.
    """
    date_to_check = date_to_check or datetime.today()
    return date_to_check.month != (date_to_check + timedelta(days=1)).month


def is_last_day_of_quarter(date_to_check=None):
    """Check if a date is the last day of its calendar quarter.

    Args:
        date_to_check: Date to check. Defaults to today.

    Returns:
        bool: True if it is the last day of the quarter.
    """
    date_to_check = date_to_check or datetime.today()
    return (QUARTER_MAP[date_to_check.month] !=
            QUARTER_MAP[(date_to_check + timedelta(days=1)).month])


def first_day_of_month(year: int, month: int):
    """Return the first day of the given month.

    Args:
        year: Year.
        month: Month number (1-12).

    Returns:
        datetime: First day of the month.
    """
    return datetime(year, month, 1)


def get_last_month():
    """Return the month and year of the previous month.

    Returns:
        tuple[int, int]: (month, year) of last month.
    """
    first_day = datetime(datetime.today().year, datetime.today().month, 1)
    last_day_of_last_month = first_day - timedelta(days=1)
    return last_day_of_last_month.month, last_day_of_last_month.year


def last_day_of_month(day: date = None, year: int = None, month: int = None):
    """Return the last day of the given month.

    Args:
        day: Reference date. Used if provided.
        year: Year (used with month if day is not provided).
        month: Month number (used with year if day is not provided).

    Returns:
        datetime: Last day of the month.

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
    if for_next:
        return last_day_of_month(day) + timedelta(days=1)
    else:
        return (day.replace(day=1) - timedelta(days=1)).replace(day=1)


def next_weekday(d, weekday):
    """Return the next occurrence of a given weekday after date d.

    Args:
        d: Reference date.
        weekday: Target weekday (0=Monday, 6=Sunday).

    Returns:
        date: The next date matching the target weekday.
    """
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def get_adjacent_dates(ref_date=None, plus=0, minus=0):
    """Return a list of dates around a reference date.

    Args:
        ref_date: Reference date. Defaults to today.
        plus: Number of days after the reference to include.
        minus: Number of days before the reference to include.

    Returns:
        list[datetime]: Dates in chronological order, including the reference.
    """
    day_range = get_offset_range(minus, plus)
    day = ref_date or datetime.today()
    return [day + timedelta(days=offset) for offset in day_range]


def is_date(_input: str, _format: str):
    """Check if a string can be parsed as a date with the given format.

    Args:
        _input: String to parse.
        _format: Date format string (e.g. ``'%Y-%m-%d'``).

    Returns:
        bool: True if the string is a valid date in the given format.
    """
    try:
        return bool(datetime.strptime(_input, _format))
    except ValueError:
        return False
