## django-reusable

[![PyPI](https://img.shields.io/pypi/v/django-reusable)](https://pypi.org/project/django-reusable/)
[![License](https://img.shields.io/pypi/l/django-reusable)](https://github.com/navedr/django-reusable/blob/master/LICENSE)

A collection of reusable utilities for Django projects.

**[Documentation](https://navedr.github.io/django-reusable/)**

### Features

- **CRUD Views** — full CRUD interface with django-tables2, filters, search, and wizard support
- **Admin Extensions** — `EnhancedAdminMixin` with action links, AJAX actions, custom buttons, multi-select filters, and theme customization
- **Model Fields** — `USAddressField`, `MultipleChoiceField`, `CurrencyField` with JSON storage and queryable components
- **Model Mixins** — `TimeStampedModel`, `MonitorChangeMixin`, `GenericRelationMixin`, `ModelUtilsMixin`
- **Forms** — custom fields, widgets, validators, and readonly form classes
- **Middleware** — login required, thread-local request, exception tracking
- **AI ORM Toolkit** — `query_model()`, `list_models_and_fields()` for LLM tool integration
- **Utilities** — 100+ functions for JSON, collections, dates, permissions, CSV export, caching, and more
- **Template Tags** — currency formatting, list splitting, dynamic formsets
- **django-tables2 Extensions** — `EnhancedTable` with extra footers, new-row columns, and custom column types

### Prerequisites

- Django >= 2.2
- django-tables2 >= 1.21.2
- django-crispy-forms >= 1.7.2
- pypugjs >= 5.6.0

### Installation

```
pip install django-reusable
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS += ("django_reusable", )
```
