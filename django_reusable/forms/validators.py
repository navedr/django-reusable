import re
from django.core.exceptions import ValidationError


def validate_percent_decimal(value):
    """
    Validates that the value is a decimal percentage between 0 and 1.

    Args:
        value (float): The value to validate.

    Raises:
        ValidationError: If the value is not between 0 and 1.
    """
    if value and (value < 0 or value > 1):
        raise ValidationError('Value should be between 0 and 1.')


def validate_percent(value):
    """
    Validates that the value is a percentage between 0 and 100.

    Args:
        value (float): The value to validate.

    Raises:
        ValidationError: If the value is not between 0 and 100.
    """
    if value and (value < 0 or value > 100):
        raise ValidationError('Value should be between 0 and 100.')


def validate_greater_than_zero(value):
    """
    Validates that the value is greater than zero.

    Args:
        value (float): The value to validate.

    Raises:
        ValidationError: If the value is not greater than zero.
    """
    if value != '' and not value > 0:
        raise ValidationError('Value should be more than 0.')


def validate_path_chars(value):
    """
    Validates that the value contains only allowed characters for a URL path.

    Args:
        value (str): The value to validate.

    Raises:
        ValidationError: If the value contains characters other than alphabets, numbers, underscore, and hyphen.
    """
    if not re.match("^[A-Za-z0-9_-]*$", value):
        raise ValidationError("URL can only contain alphabets, numbers, underscore and hyphen.")


def validate_non_negative(value):
    """
    Validates that the value is non-negative.

    Args:
        value (float): The value to validate.

    Raises:
        ValidationError: If the value is negative.
    """
    if value != '' and value < 0:
        raise ValidationError('Value cannot be negative.')
