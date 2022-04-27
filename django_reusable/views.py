import json

from django.contrib import admin
from django.http import HttpResponse
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