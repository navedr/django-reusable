"""
Verification-only settings: same app under test, but sqlite DB and suit5
instead of suit, so it can run standalone on Django 5 / Python 3.12 without
a MySQL server. Not used by the normal dev workflow (see settings.py).
"""
import os

from .settings import *  # noqa

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    'django_reusable',
    'suit5',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_tables2',
    'crispy_forms',
    'crispy_bootstrap4',
    'django_extensions',

    'company',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_TEMPLATE_PACK = 'bootstrap4'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db_verify.sqlite3'),
    },
}

STATICFILES_FINDERS = (
    'django_reusable.staticfiles.finders.DjangoReusableFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
STATIC_ROOT = os.path.join(BASE_DIR, 'static_verify')

REUSABLE_ENABLE_SUIT_MULTI_ADMIN = False
