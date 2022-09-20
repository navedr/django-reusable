THEME_COLORS = {}


def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return val


def colorscale(color_hex, scale_factor):
    """
    Scales a hex string by ``scale_factor``. Returns scaled hex string.

    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.

    >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    >>> colorscale("#52D24F", 1.6)
    #83FF7E
    >>> colorscale("#4F75D2", 1)
    #4F75D2
    """

    color_hex = color_hex.strip('#')

    if scale_factor < 0 or len(color_hex) != 6:
        return color_hex

    r, g, b = int(color_hex[:2], 16), int(color_hex[2:4], 16), int(color_hex[4:], 16)

    r = clamp(r * scale_factor)
    g = clamp(g * scale_factor)
    b = clamp(b * scale_factor)

    return "#%02x%02x%02x" % (r, g, b)


def generate_admin_theme_colors():
    from django.conf import settings

    theme_overrides = getattr(settings, 'REUSABLE_ADMIN_THEME_OVERRIDE', {})
    if theme_overrides:
        try:
            global THEME_COLORS
            if 'background_color' in theme_overrides:
                THEME_COLORS.update(dict((f'bgColor{x + 1}',
                                          colorscale(theme_overrides['background_color'], opacity))
                                         for x, opacity in enumerate([1, 2, 3])))
            if 'link_color' in theme_overrides:
                link_color = theme_overrides['link_color']
                THEME_COLORS.update(dict(
                    linkColor=link_color,
                    linkHoverColor=colorscale(link_color, 2),
                    linkVisitedColor=colorscale(link_color, 3)))
            THEME_COLORS.update(dict(
                textColor=theme_overrides.get('text_color', '')
            ))
        except Exception as e:
            print(e)
