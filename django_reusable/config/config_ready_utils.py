import inspect
import re

from django.conf import settings

from django_reusable.logging.loggers import PrintLogger
from django_reusable.utils import spaces
from django_reusable.utils.file_utils import generate_file_if_updated

try:
    from dajaxice.core import dajaxice_functions
except ImportError:
    dajaxice_functions = None

AUTO_GENERATED_COMMENT = '// This file is auto generated. Please do not edit. Your changes will be overwritten.\n\n'

DAJAXICE_STATIC_TYPES = '''
import { DajaxiceFn } from "dry-ux";

export const modules: DajaxiceModules = {};\n\n'''

PARSE_FUNCTION = ('const parse = (s: any, o: any) => Object.entries(o).reduce((s, [k, v]) => '
                  's.replace(new RegExp(":" + k, "g"), v), s);\n\n')


def generate_app_path_enums():
    file_path = getattr(settings, 'REUSABLE_APP_URL_TS_INTERFACE_PATH', None)
    if not file_path:
        return
    logger = PrintLogger("[django_reusable] generate_app_path_enums")

    def get_path(url):
        new_url = re.sub(r"%\((\w+)\)s", r":\1", url)
        pattern = r"%\((\w+)\)s"
        variables = re.findall(pattern, url)
        if variables:
            return (f'{{\n{spaces(8)}'
                    f'path: "{new_url}",\n{spaces(8)}'
                    f'get: ({": any, ".join(variables)}: any): string => '
                    f'parse("{new_url}", {{ {", ".join(variables)} }})'
                    f'\n{spaces(4)}}}')
        return f'"{new_url}"'

    from django_reusable.urls.utils import get_all_urls
    app_urls = ',\n'.join([f'{spaces(4)}"{k}": {get_path(v)}'
                           for (k, v) in sorted(get_all_urls().items(), key=lambda x: x[0])])

    content = AUTO_GENERATED_COMMENT + PARSE_FUNCTION + 'export const AppPath = {\n' + app_urls + ',\n}\n'
    generate_file_if_updated('app paths', file_path, content, logger)


def generate_dajaxice_types():
    file_path = getattr(settings, 'REUSABLE_DAJAXICE_TS_INTERFACE_PATH', None)
    if not file_path or not dajaxice_functions:
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
            return ''
        return '<{ ' + '; '.join([f"{arg}: any" for arg in args]) + ' }>'

    def get_functions(v):
        return ('{\n' + ';\n'.join([f'{spaces(8)}{name}: DajaxiceFn{get_args_type(args)}' for (name, args) in v])
                + f';\n{spaces(4)}' + '}')

    _modules = ';\n'.join([f'{spaces(4)}{k}?: {get_functions(v)}' for (k, v) in
                           sorted(modules.items(), key=lambda x: x[0])]) + ';'
    content = AUTO_GENERATED_COMMENT + DAJAXICE_STATIC_TYPES + 'export type DajaxiceModules = {\n' + _modules + '\n};\n'
    generate_file_if_updated('dajaxice types', file_path, content, logger)
