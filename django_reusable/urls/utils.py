from django.urls import get_resolver


def get_all_urls():
    result = dict()
    for (key, value) in get_resolver().reverse_dict.items():
        try:
            val = value[0][0][0]
            if isinstance(val, str) and isinstance(key, str):
                result[key] = f'/{val}'
        except:
            pass
    return result
