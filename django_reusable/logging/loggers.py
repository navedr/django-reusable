from datetime import datetime

from django.conf import settings


class PrintLogger:
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
        self._log('INFO', *message)

    def debug(self, *message):
        if settings.DEBUG or getattr(settings, 'PRINT_LOGGER_DEBUG', False):
            self._log('DEBUG', *message)

    def warn(self, *message):
        self._log('WARN', *message)

    def error(self, *message):
        self._log('ERROR', *message)
