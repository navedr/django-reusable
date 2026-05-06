"""Minimal Django settings for mkdocstrings to import django_reusable modules."""

SECRET_KEY = "docs-build-only"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_reusable",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
