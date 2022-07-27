__version__ = (0, 6, 'beta')


def apply_suit_multi_admin():
    from django.conf import settings
    if getattr(settings, 'REUSABLE_ENABLE_SUIT_MULTI_ADMIN', False):
        from django_reusable.suit_multi_admin import suit_multi_admin
        suit_multi_admin()


apply_suit_multi_admin()
