from django.contrib.auth.decorators import user_passes_test
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import Error
from .user_utils import is_superuser


@require_GET
@user_passes_test(is_superuser)
def view_list(request):
    """
    Home page that lists mose recent exceptions
    :param request: request object
    :return:  rendered template
    """
    title = "Errors"
    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1
    error = False
    errors = Error.get_exceptions_per_page(page_number=page)
    next_url = reverse('django_reusable:errors') + "?page=" + str(errors.next_num) \
        if errors.has_next else None
    prev_url = reverse('django_reusable:errors') + "?page=" + str(errors.prev_num) \
        if errors.has_prev else None

    return render(request, template_name='django_reusable/error_tracker/list.html',
                  context=dict(error=error, title=title, errors=errors,
                               next_url=next_url, prev_url=prev_url, request=request))


@require_GET
@user_passes_test(is_superuser)
def delete_exception(request, rhash):
    """
    Delete an exceptions
    :param request:  request object
    :param rhash:  hash key of the exception
    :return: redirect back to home page
    """
    Error.delete_entity(rhash)
    return redirect(reverse('django_reusable:errors'))


@require_GET
@user_passes_test(is_superuser)
def detail(request, rhash):
    """
    Display a specific page of the exception
    :param request: request object
    :param rhash:  hash key of the exception
    :return: detailed view
    """
    obj = Error.get_entity(rhash)
    error = False
    if obj is None:
        raise Http404
    title = "%s : %s" % (obj.method, obj.path)
    return render(request, template_name='django_reusable/error_tracker/detail.html',
                  context=dict(error=error, title=title, obj=obj, request=request))
