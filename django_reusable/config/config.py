import traceback

from django.apps import AppConfig

from django_reusable.config.config_ready_utils import generate_dajaxice_types, generate_app_path_enums
from django_reusable.logging.loggers import PrintLogger

try:
    from dajaxice.core import dajaxice_functions
except ImportError:
    dajaxice_functions = None


class DjangoReusableConfig(AppConfig):
    name = 'django_reusable'
    logger = PrintLogger("DjangoReusableConfig")

    def ready(self):
        methods = [
            generate_dajaxice_types,
            generate_app_path_enums,
        ]
        for method in methods:
            try:
                method()
            except:
                self.logger.error(f"Error in {method.__name__}")
                traceback.print_exc()
