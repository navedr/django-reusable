from django.template import Node, TemplateSyntaxError, Variable
from django.template.defaulttags import register
from django.utils.html import strip_tags as strip_tags_util

from django_reusable.admin.theme import THEME_COLORS
from django_reusable.utils import format_as_currency


@register.filter
def multiply(invoice, len):
    """
    Multiplies the last page count of the invoice by the given length.

    Args:
        invoice: The invoice object.
        len: The length to multiply by.

    Returns:
        The result of the multiplication.
    """
    return invoice.last_page_count * len


@register.filter
def get_item(dictionary, key):
    """
    Retrieves an item from a dictionary by key.

    Args:
        dictionary: The dictionary to retrieve the item from.
        key: The key of the item to retrieve.

    Returns:
        The value associated with the key, or None if the key is not found.
    """
    return dictionary.get(key)


@register.filter
def get_attr(obj, attr):
    """
    Retrieves an attribute from an object.

    Args:
        obj: The object to retrieve the attribute from.
        attr: The name of the attribute to retrieve.

    Returns:
        The value of the attribute, or None if the attribute is not found.
    """
    return getattr(obj, attr, None)


class SplitListNode(Node):
    """
    A template node that splits a list into sublists of a specified length.

    Args:
        original_list: The original list to split.
        items_per_list: The number of items per sublist.
        new_list: The name of the new list to store the sublists.
    """

    def __init__(self, original_list, items_per_list, new_list):
        self.original_list, self.items_per_list, self.new_list = original_list, items_per_list, new_list

    def split_seq(self, original_list, items_per_list):
        """
        Splits the original list into sublists of the specified length.

        Args:
            original_list: The original list to split.
            items_per_list: The number of items per sublist.

        Yields:
            Tuples containing the start index and the sublist.
        """
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
        """
        Renders the node by splitting the original list and storing the sublists in the context.

        Args:
            context: The template context.

        Returns:
            An empty string.
        """
        original_list = Variable(self.original_list).resolve(context)
        context[self.new_list] = self.split_seq(original_list, int(self.items_per_list))
        return ''


def divide_list(parser, token):
    """
    Parses the template tag: {% list_to_columns list as new_list 2 %}

    Args:
        parser: The template parser.
        token: The template token.

    Returns:
        A SplitListNode instance.

    Raises:
        TemplateSyntaxError: If the tag syntax is incorrect.
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
    """
    Checks if the target string is contained within the value string.

    Args:
        value: The string to search within.
        target: The string to search for.

    Returns:
        True if the target is found within the value, False otherwise.
    """
    return target.lower() in (value or '').lower()


@register.filter
def as_currency(value, decimal_precision=2):
    """
    Formats a value as currency.

    Args:
        value: The value to format.
        decimal_precision: The number of decimal places to include.

    Returns:
        The formatted currency string.
    """
    return format_as_currency(value, decimal_precision)


@register.simple_tag
def concat_all(*args):
    """
    Concatenates all arguments into a single string.

    Args:
        *args: The arguments to concatenate.

    Returns:
        The concatenated string.
    """
    return ''.join(map(str, args))


@register.filter
def strip_tags(value):
    """
    Strips HTML tags from a string.

    Args:
        value: The string to strip tags from.

    Returns:
        The string with HTML tags removed.
    """
    return strip_tags_util(value)


@register.inclusion_tag("django_reusable/dynamic-formset/formset.pug")
def dynamic_formset(formset, tabular=False, add_button_text=None):
    """
    Renders a dynamic formset.

    Args:
        formset: The formset to render.
        tabular: Whether to render the formset in tabular format.
        add_button_text: The text for the add button.

    Returns:
        A dictionary with the formset, tabular flag, and add button text.
    """
    return dict(formset=formset, tabular=tabular, add_button_text=add_button_text)


@register.filter
def replace_new_line_with_br(value):
    """
    Replaces new line characters with <br/> tags.

    Args:
        value: The string to modify.

    Returns:
        The modified string with <br/> tags.
    """
    return value.replace("\n", "<br/>")


@register.simple_tag
def theme_override_color():
    """
    Retrieves the theme override color.

    Returns:
        The theme override color.
    """
    return THEME_COLORS
