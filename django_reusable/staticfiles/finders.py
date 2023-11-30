import os
import tempfile

from django.contrib.staticfiles.finders import AppDirectoriesFinder
from django.core.exceptions import SuspiciousOperation
from django.core.files.storage import FileSystemStorage
from django.template.loader import get_template

from django_reusable.admin.theme import THEME_COLORS

FILE_OVERRIDES = {
    'admin/js/core.js': dict(
        callable='admin_core_js',
        app='django.contrib.admin',
    ),
    'suit/css/suit.css': dict(
        callable='suit_css',
        app='suit',
    ) if THEME_COLORS else None,
}


class VirtualStorage(FileSystemStorage):
    files = {}
    """" Mock a FileSystemStorage to build tmp files on demand."""

    def __init__(self, *args, **kwargs):
        self._files_cache = {}
        super(VirtualStorage, self).__init__(*args, **kwargs)

    def get_or_create_file(self, path, original_path):
        if path not in FILE_OVERRIDES:
            return ''

        with open(original_path, 'r') as admin_file:
            data = getattr(self, FILE_OVERRIDES[path]['callable'])(admin_file.read())

        try:
            current_file = open(self._files_cache[path])
            current_data = current_file.read()
            current_file.close()
            if current_data != data:
                os.remove(path)
                raise Exception("Invalid data")
        except Exception:
            filename, file_extension = os.path.splitext(path)
            handle, tmp_path = tempfile.mkstemp(file_extension)
            tmp_file = open(tmp_path, 'w')
            tmp_file.write(data)
            tmp_file.close()
            self._files_cache[path] = tmp_path

        return self._files_cache[path]

    def exists(self, name):
        return name in FILE_OVERRIDES

    def listdir(self, path):
        folders, files = [], []
        for f in FILE_OVERRIDES:
            if f.startswith(path):
                f = f.replace(path, '', 1)
                if os.sep in f:
                    folders.append(f.split(os.sep, 1)[0])
                else:
                    files.append(f)
        return folders, files

    def path(self, name, original_path=''):
        try:
            path = self.get_or_create_file(name, original_path)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        return os.path.normpath(path)


class DjangoReusableStorage(VirtualStorage):
    def admin_core_js(self, original_contents):
        admin_utils_js = get_template(os.path.join('django_reusable', 'js', 'admin-utils.js')).render()
        return original_contents + admin_utils_js

    def suit_css(self, original_contents):
        suit_theme_overrides_css = get_template(os.path.join('django_reusable', 'css', 'suit-theme-overrides.css')
                                                ).render(
            dict(theme_override_color=THEME_COLORS)) if THEME_COLORS else ''
        return original_contents + suit_theme_overrides_css


class DjangoReusableFinder(AppDirectoriesFinder):
    def find_in_app(self, app, path):
        if FILE_OVERRIDES.get(path):
            original_path = super().find_in_app(FILE_OVERRIDES[path]['app'], path)
            return DjangoReusableStorage().path(path, original_path)
        return super().find_in_app(app, path)
