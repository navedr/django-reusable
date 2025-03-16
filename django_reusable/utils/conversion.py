import math


def is_int(s):
    """
    Checks if the given string represents an integer.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string represents an integer, False otherwise.
    """
    try:
        if math.floor(float(s)) == float(s):
            return True
        else:
            return False
    except Exception:
        return False


def is_number(s):
    """
    Checks if the given string represents a number.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string represents a number, False otherwise.
    """
    try:
        float(s)
        return True
    except Exception:
        return False


def parse_int(s, default=0):
    """
    Parses the given string as an integer.

    Args:
        s (str): The string to parse.
        default (int, optional): The default value to return if parsing fails. Defaults to 0.

    Returns:
        int: The parsed integer, or the default value if parsing fails.
    """
    try:
        return int(s)
    except Exception:
        return default


def parse_float(s, default=0.0):
    """
    Parses the given string as a float.

    Args:
        s (str): The string to parse.
        default (float, optional): The default value to return if parsing fails. Defaults to 0.0.

    Returns:
        float: The parsed float, or the default value if parsing fails.
    """
    try:
        return float(s)
    except Exception:
        return default


def parse_bool(s, default=False):
    """
    Parses the given string as a boolean.

    Args:
        s (str): The string to parse.
        default (bool, optional): The default value to return if parsing fails. Defaults to False.

    Returns:
        bool: The parsed boolean, or the default value if parsing fails.
    """
    try:
        return bool(s)
    except Exception:
        return default
