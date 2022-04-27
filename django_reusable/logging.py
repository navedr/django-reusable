from datetime import datetime

from django.conf import settings


class PrintLogger:
    def __init__(self, name):
        self.name = name

    def _log(self, level, *message):
        print(f'{datetime.now()} [{level}]{" "*4} {self.name}:', *message)

    def info(self, *message):
        self._log('INFO', *message)

    def debug(self, *message):
        if settings.DEBUG:
            self._log('DEBUG', *message)

    def warn(self, *message):
        self._log('WARN', *message)

    def error(self, *message):
        self._log('ERROR', *message)
