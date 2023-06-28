import inspect

from django.conf import settings

from django_reusable.logging.loggers import PrintLogger
from django_reusable.utils.file_utils import generate_file_if_updated

try:
    from dajaxice.core import dajaxice_functions
except ImportError:
    dajaxice_functions = None

AUTO_GENERATED_COMMENT = '// This file is auto generated. Please do not edit. Your changes will be overwritten.\n'

DAJAXICE_STATIC_TYPES = '''
import { DajaxiceFn } from "dry-ux";

export const modules: DajaxiceModules = {};\n\n'''


def generate_app_path_enums():
    if not settings.REUSABLE_APP_URL_TS_INTERFACE_PATH:
        return
    logger = PrintLogger("[django_reusable] generate_app_path_enums")
    from django_reusable.urls.utils import get_all_urls
    app_urls = ',\n'.join([f'{" " * 4}"{k}" = "{v}"' for (k, v) in sorted(get_all_urls().items(),
                                                                          key=lambda x: x[0])])
    content = AUTO_GENERATED_COMMENT + 'export enum AppPath {\n' + app_urls + '\n}\n'
    generate_file_if_updated('app paths', settings.REUSABLE_APP_URL_TS_INTERFACE_PATH, content, logger)


def generate_dajaxice_types():
    if not settings.REUSABLE_DAJAXICE_TS_INTERFACE_PATH or not dajaxice_functions:
        return
    from django_reusable.urls.utils import get_all_urls
    logger = PrintLogger("[django_reusable] generate_dajaxice_types")
    get_all_urls()  # needed for dajaxice to populate its registry
    modules = dict()
    for module, submodule in dajaxice_functions.modules.submodules.items():
        if not submodule.functions.items():
            continue
        modules[module] = [(name, [x for x in inspect.getfullargspec(func.function).args if x != 'request'])
                           for name, func in submodule.functions.items()]

    def get_args_type(args):
        if not args:
            return '{}'
        return '{ ' + ', '.join([f"{arg}: any" for arg in args]) + ' }'

    def get_functions(v):
        return ('{\n' + ';\n'.join([f'{" " * 8}{name}: DajaxiceFn<{get_args_type(args)}>' for (name, args) in v])
                + f';\n{" " * 4}' + '}')

    _modules = ';\n'.join([f'{" " * 4}{k}?: {get_functions(v)}' for (k, v) in
                           sorted(modules.items(), key=lambda x: x[0])])
    content = AUTO_GENERATED_COMMENT + DAJAXICE_STATIC_TYPES + 'export type DajaxiceModules = {\n' + _modules + '\n}\n'
    generate_file_if_updated('dajaxice types', settings.REUSABLE_DAJAXICE_TS_INTERFACE_PATH, content, logger)
