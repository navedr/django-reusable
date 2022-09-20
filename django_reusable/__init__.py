__version__ = (0, 6, 'beta')

from django_reusable.admin.theme import generate_admin_theme_colors


def apply_suit_multi_admin():
    from django.conf import settings
    if getattr(settings, 'REUSABLE_ENABLE_SUIT_MULTI_ADMIN', False):
        from django_reusable.admin.suit_multi_admin import suit_multi_admin
        suit_multi_admin()


apply_suit_multi_admin()

generate_admin_theme_colors()
