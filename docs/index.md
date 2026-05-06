# django-reusable

**Agnostic and easy to use reusable library for Django**

[![PyPI](https://img.shields.io/pypi/v/django-reusable)](https://pypi.org/project/django-reusable/)
[![License](https://img.shields.io/pypi/l/django-reusable)](https://github.com/navedr/django-reusable/blob/master/LICENSE)

---

## Feature Overview

| Module | Description |
|--------|-------------|
| [Admin Mixins](api/admin-mixins.md) | Enhanced admin mixins with action links, ajax actions, extra buttons, custom fields, and theme customization |
| [Admin Filters](api/admin-filters.md) | Multi-select filters, text input filters, and search-in filters for the Django admin |
| [Admin Actions](api/admin-actions.md) | Reusable admin actions such as CSV export |
| [CRUD Views](api/views.md) | Declarative class-based CRUD views with filtering, search, permissions, and wizard support |
| [Model Mixins](api/model-mixins.md) | TimeStampedModel, MonitorChangeMixin, GenericRelationMixin, and ModelUtilsMixin |
| [Model Fields](api/model-fields.md) | USAddressField, MultipleChoiceField, CurrencyField with JSON storage |
| [Form Fields](api/form-fields.md) | Custom form fields for addresses, currency, and multi-select |
| [Form Widgets](api/form-widgets.md) | Readonly, address, currency, and date input widgets |
| [Form Classes](api/form-classes.md) | Hidden, readonly, and enhanced inline formsets |
| [Validators](api/form-validators.md) | Percent, path, and non-negative validators |
| [Middleware](api/middleware.md) | LoginRequiredMiddleware, CRequestMiddleware, and ExceptionTrackerMiddleware |
| [AI ORM Toolkit](api/ai-toolkit.md) | Dynamic LLM prompt generation and ORM query tools |
| [Tables](api/tables.md) | Enhanced django-tables2 with custom columns and footers |
| [Database](api/database.md) | CustomQuerySet, CustomManager, and post-action signals |
| [Template Tags](api/templatetags.md) | Currency formatting, list splitting, dynamic formsets |
| [Utilities](api/utils.md) | General-purpose helpers for JSON, collections, math, files, and more |
| [Date Utilities](api/date-utils.md) | Month labels, quarters, adjacent dates, day-of-month checks |
| [Decorators](api/decorators.md) | Caching and execution time logging decorators |
| [Export Utilities](api/export-utils.md) | CSV and ZIP export helpers |
| [User Utilities](api/user-utils.md) | Permission checking and user lookup helpers |
| [Logging](api/logging.md) | PrintLogger for structured console and file logging |
| [Settings Reference](settings.md) | All configurable settings in one place |

## Quick Install

```bash
pip install django-reusable
```

```python title="settings.py"
INSTALLED_APPS = [
    # ...
    'django_reusable',
]
```

See [Getting Started](getting-started.md) for full setup instructions.
