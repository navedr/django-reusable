import json
from typing import Optional, List

from django.apps import apps
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from django_reusable.logging.loggers import PrintLogger

logger = PrintLogger("DRY-ORMToolkit")


def get_project_app_labels():
    base_dir = str(settings.BASE_DIR)
    return sorted({
        config.label for config in apps.get_app_configs()
        if hasattr(config, 'path')
           and str(config.path).startswith(base_dir)
           and 'site-packages' not in str(config.path)
    })


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
    """Query a Django model using ORM filters.

    Args:
        model_name: 'app_label.model_name' (e.g. 'properties.property').
        options: dict with query options. All keys are optional:
            - filters: ORM filter kwargs (e.g. {"status": "Active", "expiry_date__lte": "2026-12-31"}).
            - exclude: ORM exclude kwargs (e.g. {"status": "Sold"}).
            - fields: list of field names for .values(). Supports FK traversal
                with __ (e.g. ["id", "tenant__name", "property_units__property__address"]).
            - order_by: list of field names for ordering. Prefix with - for descending.
            - limit: max results (default 50).
            - count_only: if true, return only the total count.
            - distinct_field: get distinct values for this field (e.g. "status").
            - aggregate: dict of aggregations. Keys are output names, values have
                'func' (count/sum/avg/min/max) and 'field'.
                Example: {"total": {"func": "sum", "field": "amount"}}
        allowed_apps: List of app labels allowed. Defaults to project apps.

    Returns:
        JSON string with query results. Always includes 'total_count' (before limit).
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
