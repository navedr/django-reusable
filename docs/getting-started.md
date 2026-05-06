# Getting Started

## Installation

```bash
pip install django-reusable
```

## Prerequisites

- **Django >= 2.0**
- **django-tables2 >= 1.21.2** (used by CRUD views)
- **django-crispy-forms >= 1.7.2** (used by form rendering)
- **pypugjs** (optional, required if using the built-in `.pug` templates)

## Configuration

### 1. Add to INSTALLED_APPS

```python title="settings.py"
INSTALLED_APPS = [
    # ...
    'django_reusable',
    'django_tables2',
    'crispy_forms',
]
```

### 2. Include URLs

```python title="urls.py"
from django.urls import path, include

urlpatterns = [
    # ...
    path('dr/', include('django_reusable.urls')),
]
```

This registers internal endpoints used by the admin mixin JS, error tracker, and utility callbacks.

## Quick Start: CRUD Views in 10 Lines

```python title="views.py"
from django_reusable.views.mixins import CRUDViews
from .models import Person

class ManagerPersonView(CRUDViews):
    base_template = 'admin/base_site.html'
    name = 'person_manager'
    model = Person
    table_fields = ['first_name', 'last_name', 'position']
    edit_fields = ['first_name', 'last_name']
    object_title = 'Person'
```

```python title="urls.py"
from django.conf.urls import url
from .views import ManagerPersonView

urlpatterns = [
    url(r'^person/', ManagerPersonView.as_view(), name='person_manager'),
]
```

This gives you a full list/create/edit/delete interface with a filterable table, edit forms, and delete confirmation -- all from a single class.

## Settings Overview

django-reusable exposes several optional settings that control admin theming, logging, TypeScript generation, and more. See the [Settings Reference](settings.md) for the complete list.
