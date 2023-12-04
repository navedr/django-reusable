import json

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def ajax_callback_handler(request, name, pk):
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
    return JsonResponse(request.user.is_authenticated, safe=False)


@csrf_exempt
def admin_utils_callback(request):
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