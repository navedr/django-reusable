from datetime import datetime
from functools import wraps

from django.conf import settings
from django.core.cache import cache

from .utils import imap
from ..logging.loggers import PrintLogger


def get_decorator_key(func, func_name, by_args, enabled, *args, **kwargs):
    """
    Generates a cache key for the decorator based on the function name and arguments.

    Args:
        func (function): The function being decorated.
        func_name (str): The name of the function.
        by_args (bool): Whether to include arguments in the key.
        enabled (bool): Whether the decorator is enabled.
        *args: Positional arguments passed to the function.
        **kwargs: Keyword arguments passed to the function.

    Returns:
        str: The generated cache key.
    """
    args_flattened = (', args:' + ','.join(imap(str, args)) + ','.join([f'{k}:{v}' for (k, v) in kwargs.items()])
                      if by_args and enabled else '')
    return f'dr:fn:{func_name or func.__name__}{args_flattened}'


def parametrized(decorator):
    """
    Decorator to wrap other decorators to preserve the arguments intellisense in IDEs.

    Args:
        decorator (function): The decorator to wrap.

    Returns:
        function: The wrapped decorator.
    """

    def layer(*args, **kwargs):
        def repl(f):
            return decorator(f, *args, **kwargs)

        return repl

    return layer


@parametrized
def cache_data(func, timeout: int, by_args=False, enabled=True, custom_cache=None):
    """
    Decorator to cache the results of the method and return cached value if it's there. Useful for expensive calculations.

    Args:
        func (function): The function to decorate.
        timeout (int): Cache timeout in seconds.
        by_args (bool): Whether to cache by arguments.
        enabled (bool): Whether to enable the caching.
        custom_cache (Cache, optional): Custom cache instance to use instead of the default Django cache.

    Returns:
        function: The decorated function.
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
    Decorator to log the execution time of the method.

    Args:
        func (function): The function to decorate.
        func_name (str, optional): Custom function name to log.
        enabled (bool): Whether to enable the logging. Can be enabled globally by setting DR_LOG_EXEC_TIME=True in Django settings.
        log_args (bool): Whether to log the arguments passed to the function.

    Returns:
        function: The decorated function.
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
