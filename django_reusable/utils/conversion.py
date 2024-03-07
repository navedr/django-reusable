import math


def is_int(s):
    try:
        if math.floor(float(s)) == float(s):
            return True
        else:
            return False
    except Exception:
        return False


def is_number(s):
    try:
        float(s)
        return True
    except Exception:
        return False


def parse_int(s, default=0):
    try:
        return int(s)
    except Exception:
        return default


def parse_float(s, default=0.0):
    try:
        return float(s)
    except Exception:
        return default


def parse_bool(s, default=False):
    try:
        return bool(s)
    except Exception:
        return default
