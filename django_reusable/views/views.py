import json

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..logging.loggers import PrintLogger


@csrf_exempt
def ajax_callback_handler(request, name, pk):
    """
    Handles AJAX callback requests.

    Args:
        request (HttpRequest): The HTTP request object.
        name (str): The name of the callback.
        pk (int): The primary key of the object.

    Returns:
        HttpResponse: The HTTP response with the callback result or an error message.
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
    """
    Checks if the user is authenticated.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response with the authentication status.
    """
    return JsonResponse(request.user.is_authenticated, safe=False)


@csrf_exempt
def admin_utils_callback(request):
    """
    Handles admin utility callback requests.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response with the utility callback result.
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
    """
    Logs a message using the specified logger.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        str: A JSON string indicating the success of the logging operation.
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
