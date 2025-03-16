from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import Permission
from django.shortcuts import resolve_url
from .utils import current_user
from django.core.exceptions import PermissionDenied
from functools import wraps
from urllib.parse import urlparse


def get_user_permissions(user):
    """
    Retrieves all permissions for the given user.

    Args:
        user (User): The user object.

    Returns:
        QuerySet: A queryset of all permissions for the user.
    """
    return user.user_permissions.all() | Permission.objects.filter(group__user=user)


def get_permissions_strings(user):
    """
    Retrieves all permissions for the given user as strings.

    Args:
        user (User): The user object.

    Returns:
        list: A list of permission strings in the format 'app_label.codename'.
    """
    return list({"%s.%s" % (ct, name) for ct, name in
                 get_user_permissions(user).values_list('content_type__app_label', 'codename')})


def get_current_user_permissions():
    """
    Retrieves all permissions for the current user.

    Returns:
        QuerySet: A queryset of all permissions for the current user.
    """
    return get_user_permissions(current_user())


def get_current_user_permissions_strings():
    """
    Retrieves all permissions for the current user as strings.

    Returns:
        list: A list of permission strings in the format 'app_label.codename'.
    """
    return get_permissions_strings(current_user())


def user_has_perms(user, perms, exclude_superuser=False):
    """
    Checks if the user has at least one permission in the list of permissions.

    Args:
        user (User): The user object.
        perms (list): A list of permissions to check.
        exclude_superuser (bool, optional): If True, superuser permissions are excluded. Defaults to False.

    Returns:
        bool: True if the user has at least one permission, False otherwise.
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
    """
    Checks if the current user has at least one permission in the list of permissions.

    Args:
        perms (list): A list of permissions to check.
        exclude_superuser (bool, optional): If True, superuser permissions are excluded. Defaults to False.

    Returns:
        bool: True if the current user has at least one permission, False otherwise.
    """
    return user_has_perms(current_user(), perms, exclude_superuser)


def get_users_for_perms(perms, user_filter=None):
    """
    Retrieves all users who have at least one of the specified permissions.

    Args:
        perms (list): A list of permissions to check.
        user_filter (dict, optional): Additional filters to apply to the user query. Defaults to None.

    Returns:
        list: A list of users who have at least one of the specified permissions.
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
    """
    Checks if the user is an active superuser.

    Args:
        user (User): The user object.

    Returns:
        bool: True if the user is an active superuser, False otherwise.
    """
    return user.is_active and user.is_staff and user.is_superuser


def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME, raise_exception=False):
    """
    Decorator for views that checks if the user passes the given test,
    redirecting to the login page if necessary.

    Args:
        test_func (function): A callable that takes the user object and returns True if the user passes.
        login_url (str, optional): The URL to redirect to for login. Defaults to settings.LOGIN_URL.
        redirect_field_name (str, optional): The name of the redirect field. Defaults to REDIRECT_FIELD_NAME.
        raise_exception (bool, optional): If True, raises PermissionDenied exception instead of redirecting. Defaults to False.

    Returns:
        function: The decorated view function.
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
