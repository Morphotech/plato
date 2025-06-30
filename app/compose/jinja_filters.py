from datetime import datetime
from typing import Union

from babel import dates
from num2words import num2words

# If a new formatter is implemented, it should be added to the FILTERS list in the __init__.py file so that it
# is loaded into the Jinja environment


def format_dates(date_str: str, format_='d MMMM yyyy') -> str:
    """
    Formats a date in ISO 8601 format to any valid babel format given as input.

    >>> format_dates('2020-01-01')
    '1 January 2020'
    >>> format_dates('2020-01-01', 'dd-MMM-yy')
    '01-Jan-20'

    To check additional formats: http://babel.pocoo.org/en/latest/dates.html#date-fields

    Args:
        date_str: The date string in ISO 8601 format
        format_: The intended format for the date, using babel syntax

    Returns: The formatted string with the specified date format, or the default one

    """
    date = datetime.fromisoformat(date_str)
    return dates.format_datetime(date, format_)


def num_to_ordinal(number: Union[int, str]) -> str:
    """
    Formats a given cardinal number (can be int or string) into an ordinal number.

    >>> num_to_ordinal(1)
    '1st'
    >>> num_to_ordinal(3)
    '3rd'
    >>> num_to_ordinal(10)
    '10th'

    Args:
        number: A cardinal number in string or int format

    Returns: The number in ordinal format, also as a string
    """
    return num2words(number, to='ordinal_num')


def nth(number: Union[str, int]) -> str:
    """
    Returns the suffix of an ordinal number, obtained from the cardinal number
    For example:
    >>> nth(1)
    'st'
    >>> nth(3)
    'rd'
    >>> nth(10)
    'th'

    Args:
        number: A cardinal number in string or int format

    Returns: The suffix of the ordinal number
    """
    return num_to_ordinal(number)[-2:]
