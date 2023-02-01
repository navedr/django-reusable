from datetime import datetime
from functools import wraps

from django.conf import settings
from django.core.cache import cache

from .utils import imap
from ..logging.loggers import PrintLogger


def get_decorator_key(func, func_name, by_args, enabled, *args, **kwargs):
    args_flattened = (', args:' + ','.join(imap(str, args)) + ','.join([f'{k}:{v}' for (k, v) in kwargs.items()])
                      if by_args and enabled else '')
    return f'fn:{func_name or func.__name__}{args_flattened}'


def parametrized(decorator):
    """
    Decorator to wrap other decorators to preserve the arguments intellisense in IDEs.
    """

    def layer(*args, **kwargs):
        def repl(f):
            return decorator(f, *args, **kwargs)

        return repl

    return layer


@parametrized
def cache_data(func, timeout: int, by_args=False, enabled=True, custom_cache=None):
    """
    Decorator to cache the results of the method and return cached value if it's there. Useful for expensive calc.

    :param func: function to decorate
    :param timeout: Cache timeout.
    :param by_args: Caches by arguments if *True*.
    :param enabled: To enable or disable it.
    :param custom_cache: To provide a custom instance of cache instead of default django one
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not enabled:
            return func(*args, **kwargs)
        key = get_decorator_key(func, None, by_args, enabled, *args, **kwargs)
        _cache = custom_cache or cache
        return _cache.get_or_set(key, lambda: func(*args, **kwargs), timeout)

    return wrapper


@parametrized
def log_exec_time(func, func_name=None, enabled=getattr(settings, 'DR_LOG_EXEC_TIME', False), log_args=False):
    """
    Decorator to log calculate the execution time of the method.

    :param func: function to decorate
    :param func_name: custom function name to log
    :param enabled: To enable or disable it. Can be enabled globally by setting DR_LOG_EXEC_TIME=True in django settings.
    :param log_args: Log arguments passed if *True*.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        key = get_decorator_key(func, func_name, log_args, enabled, *args, **kwargs)
        logger = PrintLogger(f"log_exec_time ({key})", enabled=enabled)
        start = datetime.now()
        resp = func(*args, **kwargs)
        logger.info(f'execution time={(datetime.now() - start).seconds}s')
        return resp

    return wrapper
