from datetime import datetime

from django.conf import settings


class PrintLogger:
    """
    A simple logger class that prints log messages to the console or a file.

    Attributes:
        name (str): The name of the logger.
        enabled (bool): Flag to enable or disable logging.
    """

    def __init__(self, name, enabled=True):
        """
        Initializes the PrintLogger with a name and enabled flag.

        Args:
            name (str): The name of the logger.
            enabled (bool, optional): Flag to enable or disable logging. Defaults to True.
        """
        self.name = name
        self.enabled = enabled

    def _log(self, level, *message):
        """
        Logs a message at the specified log level.

        Args:
            level (str): The log level (e.g., 'INFO', 'DEBUG', 'WARN', 'ERROR').
            *message: The message(s) to log.
        """
        if not self.enabled:
            return
        msg = ' '.join([str(m) for m in message])
        to_write = f'{datetime.now()} [{level}]{" " * 4} {self.name}: {msg}'
        if getattr(settings, 'REUSABLE_PRINT_LOGGER_FILE_PATH', None):
            with open(settings.REUSABLE_PRINT_LOGGER_FILE_PATH, 'w') as f:
                print(to_write, file=f)
        else:
            print(to_write)

    def info(self, *message):
        """
        Logs an informational message.

        Args:
            *message: The message(s) to log.
        """
        self._log('INFO', *message)

    def debug(self, *message):
        """
        Logs a debug message if debugging is enabled in settings.

        Args:
            *message: The message(s) to log.
        """
        if settings.DEBUG or getattr(settings, 'PRINT_LOGGER_DEBUG', False):
            self._log('DEBUG', *message)

    def warn(self, *message):
        """
        Logs a warning message.

        Args:
            *message: The message(s) to log.
        """
        self._log('WARN', *message)

    def error(self, *message):
        """
        Logs an error message.

        Args:
            *message: The message(s) to log.
        """
        self._log('ERROR', *message)
