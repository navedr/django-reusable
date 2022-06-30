from django.contrib.auth.models import Permission

from django_reusable.utils import current_user


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
