import json
from typing import Optional, List

from django.apps import apps
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from django_reusable.logging.loggers import PrintLogger

logger = PrintLogger("DRY-ORMToolkit")


def get_project_app_labels():
    """Return sorted app labels for project-local Django apps (excluding third-party).

    Filters out apps installed via site-packages, keeping only those whose
    path is under ``settings.BASE_DIR``.

    Returns:
        list[str]: Sorted app label strings.
    """
    base_dir = str(settings.BASE_DIR)
    return sorted({
        config.label for config in apps.get_app_configs()
        if hasattr(config, 'path')
           and str(config.path).startswith(base_dir)
           and 'site-packages' not in str(config.path)
    })


def get_app_models_summary(allowed_apps=None):
    """Generate a text summary of project apps and their models for use in LLM prompts.

    Args:
        allowed_apps: Optional list of app labels to include. Defaults to all project apps.

    Returns:
        str: Multi-line string with one line per app listing its model names.
    """
    project_apps = allowed_apps or get_project_app_labels()
    lines = []
    for label in project_apps:
        try:
            app_config = apps.get_app_config(label)
        except LookupError:
            continue
        model_names = [m.__name__ for m in app_config.get_models()]
        if model_names:
            lines.append(f'- "{label}" app: {", ".join(model_names)}')
    return '\n'.join(lines)


def _get_field_info(field):
    field_type = type(field).__name__
    info = {'name': field.name, 'type': field_type}
    if hasattr(field, 'verbose_name'):
        info['verbose_name'] = str(field.verbose_name)
    if hasattr(field, 'related_model') and field.related_model:
        info['related_model'] = field.related_model._meta.label_lower
    if hasattr(field, 'choices') and field.choices:
        info['choices'] = [c[0] for c in field.choices]
    return info


def list_models_and_fields(app_label: Optional[str] = None,
                           allowed_apps: Optional[List[str]] = None) -> str:
    """List available Django models and their fields.

    Args:
        app_label: Filter to a specific app (e.g. 'properties').
        allowed_apps: List of app labels to include. Defaults to project apps.

    Returns:
        JSON string with model schemas.
    """
    project_apps = allowed_apps or get_project_app_labels()
    if app_label:
        if app_label not in project_apps:
            return json.dumps({'error': f"App '{app_label}' is not available."})
        app_labels = [app_label]
    else:
        app_labels = sorted(project_apps)

    result = {}
    for label in app_labels:
        try:
            app_config = apps.get_app_config(label)
        except LookupError:
            continue
        for model in app_config.get_models():
            model_key = model._meta.label_lower
            fields = []
            relationships = []
            for f in model._meta.get_fields():
                if f.is_relation and not f.concrete:
                    if hasattr(f, 'related_model') and f.related_model:
                        relationships.append({
                            'name': f.name,
                            'type': type(f).__name__,
                            'related_model': f.related_model._meta.label_lower,
                        })
                else:
                    fields.append(_get_field_info(f))
            result[model_key] = {'fields': fields, 'relationships': relationships}

    return json.dumps(result, cls=DjangoJSONEncoder)


AGGREGATE_FUNCTIONS = {
    'count': models.Count,
    'sum': models.Sum,
    'avg': models.Avg,
    'min': models.Min,
    'max': models.Max,
}


def _resolve_model(model_name, allowed_apps=None):
    parts = model_name.split('.')
    if len(parts) != 2:
        return None, f"model_name must be 'app_label.model_name', got '{model_name}'"
    app_label, model_label = parts

    project_apps = allowed_apps or get_project_app_labels()
    if app_label not in project_apps:
        return None, f"App '{app_label}' is not available for querying."

    try:
        return apps.get_model(app_label, model_label), None
    except LookupError:
        return None, f"Model '{model_name}' not found."


def _build_queryset(model, filters=None, exclude=None):
    qs = model.objects.all()
    if filters:
        qs = qs.filter(**filters)
    if exclude:
        qs = qs.exclude(**exclude)
    return qs, None


def query_model(model_name: str, options: Optional[dict] = None,
                allowed_apps: Optional[List[str]] = None) -> str:
    """Query a Django model using ORM filters and return results as JSON.

    Args:
        model_name: Model identifier as ``'app_label.model_name'``
            (e.g. ``'properties.property'``).
        options: Dict with query options. All keys are optional:

            - **filters** (dict): ORM filter kwargs passed to ``.filter()``.
              Supports all Django lookups
              (e.g. ``{"status": "Active", "expiry_date__lte": "2026-12-31"}``).
            - **exclude** (dict): ORM exclude kwargs passed to ``.exclude()``
              (e.g. ``{"status": "Sold"}``).
            - **fields** (list[str]): Field names for ``.values()``. Supports FK
              traversal via ``__`` notation
              (e.g. ``["id", "tenant__name", "unit__property__address"]``).
              Defaults to all concrete non-M2M fields.
            - **order_by** (list[str]): Field names for ``.order_by()``. Prefix
              with ``-`` for descending (e.g. ``["-created_date", "name"]``).
            - **limit** (int): Maximum number of results to return. Defaults to 50.
            - **count_only** (bool): If True, return only ``{"total_count": N}``
              without fetching rows.
            - **distinct_field** (str): Return distinct values for this single field
              (e.g. ``"status"``). Returns ``{"field", "total_count", "values"}``.
            - **aggregate** (dict): Aggregation specifications. Keys are output
              names, values are dicts with ``'func'`` and ``'field'`` keys.
              Supported funcs: ``count``, ``sum``, ``avg``, ``min``, ``max``.
              Example: ``{"total": {"func": "sum", "field": "amount"}}``.

        allowed_apps: List of app labels permitted for querying. Defaults to
            project apps (auto-detected from ``settings.BASE_DIR``).

    Returns:
        str: JSON string. On success, contains ``total_count`` (count before limit),
        ``count`` (rows returned), and ``results`` (list of dicts). On error,
        contains ``{"error": "message"}``.
    """
    try:
        model, error = _resolve_model(model_name, allowed_apps)
        if error:
            return json.dumps({'error': error})

        opts = options or {}

        qs, error = _build_queryset(model, opts.get('filters'), opts.get('exclude'))
        if error:
            return json.dumps({'error': error})

        total_count = qs.count()

        if opts.get('count_only'):
            return json.dumps({'total_count': total_count}, cls=DjangoJSONEncoder)

        distinct_field = opts.get('distinct_field')
        if distinct_field:
            values = list(qs.values_list(distinct_field, flat=True).distinct().order_by(distinct_field))
            return json.dumps({'field': distinct_field, 'total_count': len(values), 'values': values},
                              cls=DjangoJSONEncoder)

        aggregate = opts.get('aggregate')
        if aggregate:
            agg_kwargs = {}
            for name, spec in aggregate.items():
                func = AGGREGATE_FUNCTIONS.get(spec['func'].lower())
                if not func:
                    return json.dumps({'error': f"Unknown aggregate function: {spec['func']}"})
                agg_kwargs[name] = func(spec['field'])
            result = qs.aggregate(**agg_kwargs)
            result['total_count'] = total_count
            return json.dumps(result, cls=DjangoJSONEncoder)

        order_by = opts.get('order_by')
        if order_by:
            qs = qs.order_by(*order_by)

        limit = opts.get('limit', 50)
        qs = qs[:limit]

        fields = opts.get('fields')
        if fields:
            data = list(qs.values(*fields))
        else:
            concrete_fields = [
                f.name for f in model._meta.get_fields()
                if f.concrete and not f.many_to_many
            ]
            data = list(qs.values(*concrete_fields))

        return json.dumps({'total_count': total_count, 'count': len(data), 'results': data}, cls=DjangoJSONEncoder)

    except Exception as e:
        logger.error(f"query_model failed: model={model_name}, error={e}")
        return json.dumps({'error': str(e)})
