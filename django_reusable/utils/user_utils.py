from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import Permission
from django.shortcuts import resolve_url
from .utils import current_user
from django.core.exceptions import PermissionDenied
from functools import wraps
from urllib.parse import urlparse

def get_user_permissions(user):
    """Return all permissions for a user, including group-inherited ones.

    Args:
        user: Django User instance.

    Returns:
        QuerySet: Combined user and group permissions.
    """
    return user.user_permissions.all() | Permission.objects.filter(group__user=user)


def get_permissions_strings(user):
    """Return permission strings in ``'app_label.codename'`` format for a user.

    Args:
        user: Django User instance.

    Returns:
        list[str]: Unique permission strings.
    """
    return list({"%s.%s" % (ct, name) for ct, name in
                 get_user_permissions(user).values_list('content_type__app_label', 'codename')})


def get_current_user_permissions():
    """Return all permissions for the currently authenticated user.

    Returns:
        QuerySet: Combined user and group permissions.
    """
    return get_user_permissions(current_user())


def get_current_user_permissions_strings():
    """Return permission strings for the currently authenticated user.

    Returns:
        list[str]: Permission strings in ``'app_label.codename'`` format.
    """
    return get_permissions_strings(current_user())


def user_has_perms(user, perms, exclude_superuser=False):
    """Check if a user has at least one of the given permissions.

    Args:
        user: Django User instance.
        perms: List of permission strings (e.g. ``['app.add_model', 'app.change_model']``).
        exclude_superuser: If True, do not auto-grant for superusers; check
            actual permissions instead. Defaults to False.

    Returns:
        bool: True if the user has at least one of the listed permissions.
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
    """Check if the current user has at least one of the given permissions.

    Args:
        perms: List of permission strings.
        exclude_superuser: If True, check actual permissions even for superusers.

    Returns:
        bool: True if the current user has at least one permission.
    """
    return user_has_perms(current_user(), perms, exclude_superuser)


def get_users_for_perms(perms, user_filter=None):
    """Return all users who have at least one of the given permissions.

    Includes users who have the permission directly or via group membership.

    Args:
        perms: List of permission strings (e.g. ``['app.view_model']``).
        user_filter: Optional dict of ORM filter kwargs to apply to user querysets.

    Returns:
        list[User]: Users with matching permissions.
    """
    users = set()
    user_filter = user_filter or {}
    for perm in perms:
        app_label, perm_name = perm.split('.')
        permission = Permission.objects.filter(content_type__app_label=app_label, codename=perm_name).first()
        if permission:
            users.update(list(permission.user_set.filter(**user_filter)))
            for group in permission.group_set.all():
                users.update(list(group.user_set.filter(**user_filter)))
    return list(users)


def is_superuser(user):
    """Check if a user is an active staff superuser.

    Args:
        user: Django User instance.

    Returns:
        bool: True if user is active, staff, and superuser.
    """
    return user.is_active and user.is_staff and user.is_superuser


def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME, raise_exception=False):
    """View decorator that checks the user against a test function.

    Redirects to the login page if the test fails, or raises ``PermissionDenied``
    if ``raise_exception`` is True.

    Args:
        test_func: Callable that takes a User and returns True if access is allowed.
        login_url: URL to redirect to on failure. Defaults to ``settings.LOGIN_URL``.
        redirect_field_name: Query parameter name for the redirect URL.
        raise_exception: If True, raise ``PermissionDenied`` instead of redirecting.

    Returns:
        Callable: Decorated view function.

    Example:
        ```python
        @user_passes_test(lambda u: u.is_staff)
        def staff_view(request):
            ...
        ```
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
