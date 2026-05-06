# Settings Reference

All settings are optional. Add them to your Django `settings.py` as needed.

| Setting | Default | Description | Module |
|---------|---------|-------------|--------|
| `REUSABLE_ENABLE_SUIT_MULTI_ADMIN` | `False` | Enable django-suit multi-admin site support | `django_reusable.__init__` |
| `REUSABLE_ADMIN_THEME_OVERRIDE` | `{}` | Dict with `background_color`, `link_color`, and/or `text_color` keys to customize admin theme colors | `django_reusable.admin.theme` |
| `REUSABLE_READONLY_PERM_PREFIX` | `None` | Permission prefix used to determine if save buttons should be hidden on admin change forms | `django_reusable.views.views` |
| `REUSABLE_TS_UTIL_ENABLED` | `True` | Enable TypeScript utility generation on app ready | `django_reusable.config.config` |
| `REUSABLE_APP_URL_TS_INTERFACE_PATH` | `None` | File path for generated TypeScript app URL interface | `django_reusable.config.config_ready_utils` |
| `REUSABLE_DAJAXICE_TS_INTERFACE_PATH` | `None` | File path for generated TypeScript Dajaxice interface | `django_reusable.config.config_ready_utils` |
| `REUSABLE_PY_TO_TS_MAP` | `{}` | Configuration map for Python-to-TypeScript type generation | `django_reusable.config.config_ready_utils` |
| `REUSABLE_PRINT_LOGGER_FILE_PATH` | `None` | File path for PrintLogger output; when set, logs are written to this file | `django_reusable.logging.loggers` |
| `REUSABLE_SHOW_ERRORS_LINK` | `False` | Show an "Errors" link in the suit multi-admin menu | `django_reusable.admin.suit_multi_admin` |
| `REUSABLE_SHOW_ERRORS_PERM` | `'django_reusable.view_errors'` | Permission required to view the errors link | `django_reusable.admin.suit_multi_admin` |
| `DR_LOG_EXEC_TIME` | `False` | Enable execution time logging for functions decorated with `@log_exec_time` | `django_reusable.utils.decorators` |
| `PRINT_LOGGER_DEBUG` | `False` | Enable PrintLogger output even when `DEBUG` is `False` | `django_reusable.logging.loggers` |
| `LOGIN_URL` | (Django default) | Used by `LoginRequiredMiddleware` as the redirect target for unauthenticated users | `django_reusable.middleware.middleware` |
| `OPEN_URLS` | `{}` | Dict of URL patterns that bypass `LoginRequiredMiddleware` authentication checks | `django_reusable.middleware.middleware` |
| `CURRENT_HOST` | `None` | Override the host used by `get_absolute_url()` utility | `django_reusable.utils.utils` |

## Example

```python title="settings.py"
# Theme customization
REUSABLE_ADMIN_THEME_OVERRIDE = {
    'background_color': '#1a237e',
    'link_color': '#42a5f5',
    'text_color': '#ffffff',
}

# Logging
REUSABLE_PRINT_LOGGER_FILE_PATH = '/var/log/myapp/print.log'
DR_LOG_EXEC_TIME = True

# Middleware
LOGIN_URL = '/accounts/login/'
OPEN_URLS = {
    'api': r'^/api/',
    'health': r'^/health/',
}
```
