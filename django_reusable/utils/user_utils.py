from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import Permission
from django.shortcuts import resolve_url
from .utils import current_user
from django.core.exceptions import PermissionDenied
from functools import wraps
from urllib.parse import urlparse

def get_user_permissions(user):
    return user.user_permissions.all() | Permission.objects.filter(group__user=user)


def get_permissions_strings(user):
    return list({"%s.%s" % (ct, name) for ct, name in
                 get_user_permissions(user).values_list('content_type__app_label', 'codename')})


def get_current_user_permissions():
    return get_user_permissions(current_user())


def get_current_user_permissions_strings():
    return get_permissions_strings(current_user())


def user_has_perms(user, perms, exclude_superuser=False):
    """
    Checks if the user has at least one perm in the list of perms
    :param user:
    :param perms: Perms to check
    :param exclude_superuser: By default, superuser has all perms. If this is True, then it checks permissions list.
    :return: True if user has at least one perm
    """
    if not exclude_superuser and user.is_superuser:
        return True
    if exclude_superuser:
        user_permissions = get_permissions_strings(user)
        has_perms = [perm in user_permissions for perm in perms]
    else:
        has_perms = [user.has_perm(perm) for perm in perms]
    return not not list(filter(None, has_perms))


def current_user_has_perms(perms, exclude_superuser=False):
    return user_has_perms(current_user(), perms, exclude_superuser)


def get_users_for_perms(perms):
    users = set()
    for perm in perms:
        app_label, perm_name = perm.split('.')
        permission = Permission.objects.filter(content_type__app_label=app_label, codename=perm_name).first()
        if permission:
            users.update(list(permission.user_set.all()))
            for group in permission.group_set.all():
                users.update(list(group.user_set.all()))
    return list(users)


def is_superuser(user):
    return user.is_active and user.is_staff and user.is_superuser


def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME, raise_exception=False):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            from django.contrib.auth.views import redirect_to_login
            if raise_exception:
                raise PermissionDenied
            return redirect_to_login(
                path, resolved_login_url, redirect_field_name)

        return _wrapped_view

    return decorator
