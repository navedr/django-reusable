from django.urls import get_resolver, resolve, reverse

from django_reusable.constants import URLNames


def get_all_urls():
    """
    Retrieves all URL patterns and their corresponding paths.

    Returns:
        dict: A dictionary where the keys are URL names and the values are their paths.
    """
    result = dict()
    for (key, value) in get_resolver().reverse_dict.items():
        try:
            val = value[0][0][0]
            if isinstance(val, str) and isinstance(key, str):
                result[key] = f'/{val}'
        except:
            pass
    try:
        result[URLNames.IS_USER_AUTHENTICATED] = reverse(f"django_reusable:{URLNames.IS_USER_AUTHENTICATED}")
    except:
        pass
    return result


def get_app_and_url_name(request):
    """
    Retrieves the app name and URL name from the request.

    Args:
        request (HttpRequest): The current request object.

    Returns:
        tuple: A tuple containing the app name and URL name.
    """
    try:
        resolved = resolve(request.path_info)
        return resolved.app_name, resolved.url_name
    except:
        return '', ''
