import json

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..logging.loggers import PrintLogger


@csrf_exempt
def ajax_callback_handler(request, name, pk):
    """Handle AJAX callback requests dispatched by admin action buttons.

    Args:
        request: The current ``HttpRequest`` (POST body parsed as JSON kwargs).
        name: Registered callback name.
        pk: Primary key of the target object.

    Returns:
        ``HttpResponse`` with the callback's return value, or an error message.
    """
    callback_params = getattr(admin.site, 'ajax_handler_callback_params', {}).get(name)
    if callback_params:
        self, callback = callback_params
        kwargs = json.loads(request.body)
        kwargs.update(dict(
            pk=pk,
            self=self
        ))
        return HttpResponse(callback(**kwargs))
    return HttpResponse(f'no callback params defined for {name}')


@csrf_exempt
def is_user_authenticated(request):
    """Return a JSON boolean indicating whether the current user is authenticated."""
    return JsonResponse(request.user.is_authenticated, safe=False)


@csrf_exempt
def admin_utils_callback(request):
    """Utility endpoint for admin JS to check permissions and UI state.

    Reads ``REUSABLE_READONLY_PERM_PREFIX`` from settings and returns a JSON
    object with flags like ``hide_save_buttons`` based on the current user's
    permissions.
    """
    payload = json.loads(request.body)
    app = payload.get('app')
    model = payload.get('model')
    is_changelist = payload.get('isChangelist')
    is_change_form = payload.get('isChangeForm')
    response = dict()
    if is_change_form:
        response.update(
            hide_save_buttons=getattr(settings, 'REUSABLE_READONLY_PERM_PREFIX', None) and
                              not request.user.is_superuser and
                              request.user.has_perm(f'{app}.{settings.REUSABLE_READONLY_PERM_PREFIX}{model}')
        )
    return JsonResponse(response, safe=False)


@csrf_exempt
def log(request):
    """Server-side logging endpoint for frontend JavaScript.

    Accepts a JSON body with ``logger_name``, ``level`` (info/debug/warn/error),
    and ``message``, then logs via ``PrintLogger``.
    """
    payload = json.loads(request.body)
    logger_name = payload.get('logger_name')
    level = payload.get('level')
    message = payload.get('message')
    logger = PrintLogger(logger_name)
    if level == 'info':
        logger.info(message)
    elif level == 'debug':
        logger.debug(message)
    elif level == 'warn':
        logger.warn(message)
    elif level == 'error':
        logger.error(message)
    return json.dumps(dict(success=True))
