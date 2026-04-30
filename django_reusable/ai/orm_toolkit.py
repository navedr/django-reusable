import json
from typing import Optional, List

from django.apps import apps
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

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


def query_model(model_name: str, filters: Optional[str] = None,
                fields: Optional[str] = None, order_by: Optional[str] = None,
                limit: int = 50, allowed_apps: Optional[List[str]] = None) -> str:
    """Query a Django model using ORM filters.

    Args:
        model_name: 'app_label.model_name' (e.g. 'properties.property').
        filters: JSON string of ORM filter kwargs.
        fields: Comma-separated field names for .values(). Omit for all concrete fields.
        order_by: Comma-separated field names for ordering. Prefix with - for descending.
        limit: Max results (default 50).
        allowed_apps: List of app labels allowed. Defaults to project apps.

    Returns:
        JSON string with query results.
    """
    try:
        parts = model_name.split('.')
        if len(parts) != 2:
            return json.dumps({'error': f"model_name must be 'app_label.model_name', got '{model_name}'"})
        app_label, model_label = parts

        project_apps = allowed_apps or get_project_app_labels()
        if app_label not in project_apps:
            return json.dumps({'error': f"App '{app_label}' is not available for querying."})

        try:
            model = apps.get_model(app_label, model_label)
        except LookupError:
            return json.dumps({'error': f"Model '{model_name}' not found."})

        qs = model.objects.all()

        if filters:
            try:
                filter_kwargs = json.loads(filters)
            except json.JSONDecodeError:
                return json.dumps({'error': f"Invalid filters JSON: {filters}"})
            qs = qs.filter(**filter_kwargs)

        if order_by:
            qs = qs.order_by(*[f.strip() for f in order_by.split(',')])

        qs = qs[:limit]

        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            data = list(qs.values(*field_list))
        else:
            concrete_fields = [
                f.name for f in model._meta.get_fields()
                if f.concrete and not f.many_to_many
            ]
            data = list(qs.values(*concrete_fields))

        return json.dumps({'count': len(data), 'results': data}, cls=DjangoJSONEncoder)

    except Exception as e:
        logger.error(f"query_model failed: model={model_name}, error={e}")
        return json.dumps({'error': str(e)})
