from datetime import datetime

from django.conf import settings


class PrintLogger:
    """Simple logger that writes timestamped messages to stdout or a file.

    Outputs to ``settings.REUSABLE_PRINT_LOGGER_FILE_PATH`` if configured,
    otherwise prints to stdout. Debug messages require ``settings.DEBUG``
    or ``settings.PRINT_LOGGER_DEBUG`` to be True.

    Args:
        name: Logger name included in all output lines.
        enabled: If False, all log calls are silently ignored.
    """

    def __init__(self, name, enabled=True):
        self.name = name
        self.enabled = enabled

    def _log(self, level, *message):
        if not self.enabled:
            return
        msg = ' '.join([str(m) for m in message])
        to_write = f'{datetime.now()} [{level}]{" "*4} {self.name}: {msg}'
        if getattr(settings, 'REUSABLE_PRINT_LOGGER_FILE_PATH', None):
            with open(settings.REUSABLE_PRINT_LOGGER_FILE_PATH, 'w') as f:
                print(to_write, file=f)
        else:
            print(to_write)

    def info(self, *message):
        """Log an INFO-level message."""
        self._log('INFO', *message)

    def debug(self, *message):
        """Log a DEBUG-level message (only when DEBUG or PRINT_LOGGER_DEBUG is True)."""
        if settings.DEBUG or getattr(settings, 'PRINT_LOGGER_DEBUG', False):
            self._log('DEBUG', *message)

    def warn(self, *message):
        """Log a WARN-level message."""
        self._log('WARN', *message)

    def error(self, *message):
        """Log an ERROR-level message."""
        self._log('ERROR', *message)
