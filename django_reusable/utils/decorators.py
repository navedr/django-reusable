from datetime import datetime
from functools import wraps

from django.conf import settings
from django.core.cache import cache

from .utils import imap
from ..logging.loggers import PrintLogger


def get_decorator_key(func, func_name, by_args, enabled, *args, **kwargs):
    args_flattened = (', args:' + ','.join(imap(str, args)) + ','.join([f'{k}:{v}' for (k, v) in kwargs.items()])
                      if by_args and enabled else '')
    return f'dr:fn:{func_name or func.__name__}{args_flattened}'


def parametrized(decorator):
    """Meta-decorator that allows decorators to accept arguments while preserving IDE intellisense.

    Args:
        decorator: The decorator function to wrap.

    Returns:
        Callable: A wrapper that accepts decorator arguments and returns the decorated function.

    Example:
        ```python
        @parametrized
        def my_decorator(func, arg1, arg2=True):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        @my_decorator(arg1='value')
        def my_func():
            pass
        ```
    """

    def layer(*args, **kwargs):
        def repl(f):
            return decorator(f, *args, **kwargs)

        return repl

    return layer


@parametrized
def cache_data(func, timeout: int, by_args=False, enabled=True, custom_cache=None):
    """Cache the return value of a function using Django's cache framework.

    Useful for expensive calculations or database queries.

    Args:
        func: The function to decorate (injected by ``@parametrized``).
        timeout: Cache timeout in seconds.
        by_args: If True, cache separately per unique arguments. Defaults to False.
        enabled: Toggle caching on/off. Defaults to True.
        custom_cache: Optional custom cache backend instance. Defaults to Django's default cache.

    Returns:
        Callable: Wrapped function with caching.

    Example:
        ```python
        @cache_data(timeout=3600, by_args=True)
        def get_expensive_data(user_id):
            return compute(user_id)
        ```
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
    """Log the execution time of a function via PrintLogger.

    Can be enabled globally by setting ``DR_LOG_EXEC_TIME = True`` in Django settings.

    Args:
        func: The function to decorate (injected by ``@parametrized``).
        func_name: Custom name for log output. Defaults to the function's ``__name__``.
        enabled: Toggle logging on/off. Defaults to ``settings.DR_LOG_EXEC_TIME``.
        log_args: If True, include function arguments in the log key.

    Returns:
        Callable: Wrapped function that logs its execution time.

    Example:
        ```python
        @log_exec_time(func_name='my_task', log_args=True)
        def process_data(items):
            ...
        ```
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
