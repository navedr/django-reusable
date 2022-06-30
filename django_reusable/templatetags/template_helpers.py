from django.template import Node, TemplateSyntaxError, Variable
from django.template.defaulttags import register

from django.utils.html import strip_tags as strip_tags_util

from django_reusable.utils import format_as_currency


@register.filter
def multiply(invoice, len):
    return invoice.last_page_count * len


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr, None)


class SplitListNode(Node):
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
    """Parse template tag: {% list_to_columns list as new_list 2 %}"""
    bits = token.contents.split()
    if len(bits) != 5:
        raise TemplateSyntaxError("list_to_columns list as new_list 2")
    if bits[2] != 'as':
        raise TemplateSyntaxError("second argument to the list_to_columns tag must be 'as'")
    return SplitListNode(bits[1], bits[4], bits[3])


divide_list = register.tag(divide_list)


@register.filter
def contains(value, target):
    return target.lower() in (value or '').lower()


@register.filter
def as_currency(value, decimal_precision=2):
    return format_as_currency(value, decimal_precision)


@register.simple_tag
def concat_all(*args):
    """concatenate all args"""
    return ''.join(map(str, args))


@register.filter
def strip_tags(value):
    return strip_tags_util(value)


@register.inclusion_tag("django_reusable/dynamic-formset/formset.pug")
def dynamic_formset(formset, tabular=False, add_button_text=None):
    return dict(formset=formset, tabular=tabular, add_button_text=add_button_text)


@register.filter
def replace_new_line_with_br(value):
    return value.replace("\n", "<br/>")