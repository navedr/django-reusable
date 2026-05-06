from django.template import Node, TemplateSyntaxError, Variable
from django.template.defaulttags import register
from django.utils.html import strip_tags as strip_tags_util

from django_reusable.admin.theme import THEME_COLORS
from django_reusable.utils import format_as_currency


@register.filter
def multiply(invoice, len):
    """Multiply an invoice's last_page_count by the given length."""
    return invoice.last_page_count * len


@register.filter
def get_item(dictionary, key):
    """Template filter to access a dictionary value by key.

    Usage: ``{{ my_dict|get_item:key_var }}``
    """
    return dictionary.get(key)


@register.filter
def get_attr(obj, attr):
    """Template filter to access an object attribute by name.

    Usage: ``{{ my_obj|get_attr:"field_name" }}``
    """
    return getattr(obj, attr, None)


class SplitListNode(Node):
    """Template node that splits a list into chunks of a given size."""

    def __init__(self, original_list, items_per_list, new_list):
        self.original_list, self.items_per_list, self.new_list = original_list, items_per_list, new_list

    def split_seq(self, original_list, items_per_list):
        start = 0
        original_list = list(original_list or [])
        while True:
            stop = start + items_per_list
            part = original_list[start:stop]
            if part:
                yield start, part
                start = stop
            else:
                break

    def render(self, context):
        original_list = Variable(self.original_list).resolve(context)
        context[self.new_list] = self.split_seq(original_list, int(self.items_per_list))
        return ''


def divide_list(parser, token):
    """Split a list into chunks for column-based rendering.

    Usage: ``{% list_to_columns my_list as chunked_list 3 %}``

    Args:
        parser: Django template parser.
        token: Template tag token.

    Returns:
        SplitListNode: Node that splits the list in the template context.
    """
    bits = token.contents.split()
    if len(bits) != 5:
        raise TemplateSyntaxError("list_to_columns list as new_list 2")
    if bits[2] != 'as':
        raise TemplateSyntaxError("second argument to the list_to_columns tag must be 'as'")
    return SplitListNode(bits[1], bits[4], bits[3])


divide_list = register.tag(divide_list)


@register.filter
def contains(value, target):
    """Case-insensitive substring check.

    Usage: ``{{ value|contains:"search" }}``
    """
    return target.lower() in (value or '').lower()


@register.filter
def as_currency(value, decimal_precision=2):
    """Format a value as currency with the given decimal precision.

    Usage: ``{{ amount|as_currency }}`` or ``{{ amount|as_currency:0 }}``
    """
    return format_as_currency(value, decimal_precision)


@register.simple_tag
def concat_all(*args):
    """concatenate all args"""
    return ''.join(map(str, args))


@register.filter
def strip_tags(value):
    """Remove all HTML tags from a string.

    Usage: ``{{ html_content|strip_tags }}``
    """
    return strip_tags_util(value)


@register.inclusion_tag("django_reusable/dynamic-formset/formset.pug")
def dynamic_formset(formset, tabular=False, add_button_text=None):
    """Render a dynamic Django formset with add/remove functionality.

    Args:
        formset: Django formset instance.
        tabular: If True, render in tabular layout.
        add_button_text: Custom text for the add button.
    """
    return dict(formset=formset, tabular=tabular, add_button_text=add_button_text)


@register.filter
def replace_new_line_with_br(value):
    """Replace newline characters with ``<br/>`` HTML tags.

    Usage: ``{{ text|replace_new_line_with_br }}``
    """
    return value.replace("\n", "<br/>")


@register.simple_tag
def theme_override_color():
    """Return the configured theme override colors from admin theme settings."""
    return THEME_COLORS
