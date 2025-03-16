import os
import tempfile

from django.contrib.staticfiles.finders import AppDirectoriesFinder
from django.core.exceptions import SuspiciousOperation
from django.core.files.storage import FileSystemStorage
from django.template.loader import get_template
from django.urls import reverse

from django_reusable.admin.theme import THEME_COLORS
from django_reusable.constants import URLNames

FILE_OVERRIDES = {
    'admin/js/core.js': 'admin_core_js',
    'suit/css/suit.css': 'suit_css' if THEME_COLORS else None,
}


class VirtualStorage(FileSystemStorage):
    """
    A custom FileSystemStorage that creates temporary files on demand.

    Attributes:
        files (dict): A dictionary to mock file storage.
        _files_cache (dict): A cache to store temporary file paths.
        original_storage (FileSystemStorage): The original storage backend.
    """
    files = {}
    """" Mock a FileSystemStorage to build tmp files on demand."""

    def __init__(self, *args, **kwargs):
        """
        Initializes the VirtualStorage with optional original storage.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self._files_cache = {}
        self.original_storage = kwargs.pop('original_storage', None)
        super(VirtualStorage, self).__init__(*args, **kwargs)

    def get_or_create_file(self, path, original_path):
        """
        Gets or creates a temporary file for the given path.

        Args:
            path (str): The path of the file.
            original_path (str): The original path of the file.

        Returns:
            str: The path to the temporary file.
        """
        if path not in FILE_OVERRIDES:
            return ''

        with open(original_path, 'r') as original_file:
            data = getattr(self, FILE_OVERRIDES[path])(original_file.read())

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
        """
        Checks if the file exists in the overrides.

        Args:
            name (str): The name of the file.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return name in FILE_OVERRIDES

    def listdir(self, path):
        """
        Lists directories and files under the given path.

        Args:
            path (str): The path to list.

        Returns:
            tuple: A tuple containing lists of folders and files.
        """
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
        """
        Gets the path to the file, creating it if necessary.

        Args:
            name (str): The name of the file.
            original_path (str, optional): The original path of the file. Defaults to ''.

        Returns:
            str: The normalized path to the file.

        Raises:
            SuspiciousOperation: If access to the file is denied.
        """
        if not original_path and self.original_storage:
            original_path = self.original_storage.path(name)
        try:
            path = self.get_or_create_file(name, original_path)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        return os.path.normpath(path)


class DjangoReusableStorage(VirtualStorage):
    """
    A custom storage that extends VirtualStorage to handle specific file overrides.
    """

    def admin_core_js(self, original_contents):
        """
        Appends admin utility JavaScript to the original contents.

        Args:
            original_contents (str): The original file contents.

        Returns:
            str: The modified file contents.
        """
        admin_utils_js = get_template(os.path.join('django_reusable', 'js', 'admin-utils.js')).render(
            dict(admin_utils_url=reverse(f'django_reusable:{URLNames.ADMIN_UTILS_JS_CALLBACK}')))
        return original_contents + admin_utils_js

    def suit_css(self, original_contents):
        """
        Appends suit theme overrides CSS to the original contents.

        Args:
            original_contents (str): The original file contents.

        Returns:
            str: The modified file contents.
        """
        suit_theme_overrides_css = get_template(os.path.join('django_reusable', 'css', 'suit-theme-overrides.css')
                                                ).render(
            dict(theme_override_color=THEME_COLORS)) if THEME_COLORS else ''
        return original_contents + suit_theme_overrides_css


class DjangoReusableFinder(AppDirectoriesFinder):
    """
    A custom static files finder that uses DjangoReusableStorage for specific file overrides.
    """

    def find_in_app(self, app, path):
        """
        Finds the file in the app directories, using DjangoReusableStorage if necessary.

        Args:
            app (str): The app name.
            path (str): The file path.

        Returns:
            str: The path to the file or None if not found.
        """
        original_path = super().find_in_app(app, path)
        if FILE_OVERRIDES.get(path) and original_path:
            return DjangoReusableStorage().path(path, original_path)
        return original_path

    def list(self, ignore_patterns):
        """
        Lists all files in the app directories, using DjangoReusableStorage for specific overrides.

        Args:
            ignore_patterns (list): A list of patterns to ignore.

        Yields:
            tuple: A tuple containing the file path and storage.
        """
        for path, storage in super().list(ignore_patterns):
            yield path, DjangoReusableStorage(original_storage=storage) if FILE_OVERRIDES.get(path) else storage
