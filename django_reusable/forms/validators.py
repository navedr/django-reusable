import re
from django.core.exceptions import ValidationError


def validate_percent_decimal(value):
    if value and (value < 0 or value > 1):
        raise ValidationError('Value should be between 0 and 1.')


def validate_percent(value):
    if value and (value < 0 or value > 100):
        raise ValidationError('Value should be between 0 and 100.')


def validate_greater_than_zero(value):
    if value != '' and not value > 0:
        raise ValidationError('Value should be more than 0.')


def validate_path_chars(value):
    if not re.match("^[A-Za-z0-9_-]*$", value):
        raise ValidationError("URL can only contain alphabets, numbers, underscore and hyphen.")


def validate_non_negative(value):
    if value != '' and value < 0:
        raise ValidationError('Value cannot be negative.')
