import re
from django.core.exceptions import ValidationError


def validate_percent_decimal(value):
    """Validate that a value is between 0 and 1 (inclusive).

    Use for percentage fields stored as decimals (e.g. 0.75 = 75%).

    Args:
        value: Numeric value to validate.

    Raises:
        ValidationError: If value is outside the 0-1 range.
    """
    if value and (value < 0 or value > 1):
        raise ValidationError('Value should be between 0 and 1.')


def validate_percent(value):
    """Validate that a value is between 0 and 100 (inclusive).

    Use for percentage fields stored as whole numbers (e.g. 75 = 75%).

    Args:
        value: Numeric value to validate.

    Raises:
        ValidationError: If value is outside the 0-100 range.
    """
    if value and (value < 0 or value > 100):
        raise ValidationError('Value should be between 0 and 100.')


def validate_greater_than_zero(value):
    """Validate that a value is strictly greater than zero.

    Args:
        value: Numeric value to validate. Empty strings are allowed.

    Raises:
        ValidationError: If value is zero or negative.
    """
    if value != '' and not value > 0:
        raise ValidationError('Value should be more than 0.')


def validate_path_chars(value):
    """Validate that a string contains only URL-safe path characters.

    Allows letters, digits, underscores, and hyphens only.

    Args:
        value: String value to validate.

    Raises:
        ValidationError: If value contains characters other than ``[A-Za-z0-9_-]``.
    """
    if not re.match("^[A-Za-z0-9_-]*$", value):
        raise ValidationError("URL can only contain alphabets, numbers, underscore and hyphen.")


def validate_non_negative(value):
    """Validate that a value is zero or positive.

    Args:
        value: Numeric value to validate. Empty strings are allowed.

    Raises:
        ValidationError: If value is negative.
    """
    if value != '' and value < 0:
        raise ValidationError('Value cannot be negative.')
