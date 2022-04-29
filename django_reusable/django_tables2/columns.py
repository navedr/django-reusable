import itertools

from django import forms
from django.utils.safestring import mark_safe
from django_tables2 import CheckBoxColumn as DefaultCheckBoxColumn, Column
from django_tables2.utils import AttributeDict

from django_reusable.utils import global_request, humane_currency, format_as_currency
from django_reusable.widgets import ReadOnlyInput


class TextFieldColumn(Column):
    empty_values = []

    def render(self, value):
        ff = forms.CharField(widget=forms.Textarea)
        ff.widget.attrs['class'] = 'form-control'
        return ff.widget.render(self.verbose_name, value)


class EnhancedCheckBoxColumn(DefaultCheckBoxColumn):
    def select_checked(self, value, record):
        request = global_request()
        selected_ids = dict(request.POST).get(self.bound_column, [])
        return str(value) in selected_ids

    def __init__(self, header=None, attrs=None, checked=None, bound_column=None, **extra):
        self._header = header
        self.bound_column = bound_column
        checked = checked or self.select_checked
        super().__init__(attrs, checked, **extra)

    @property
    def header(self):
        attrs = self.attrs.get("th__input", {})
        attrs["onchange"] = '''$(this).parents('table').find(
        `tr td:nth-child(${$(this).parents("th").index() + 1}) input`
        ).prop("checked", this.checked);
        '''
        self.attrs["th__input"] = attrs
        header = self._header or super().header
        return header


class RadioButtonColumn(DefaultCheckBoxColumn):
    @property
    def header(self):
        return ''

    def render(self, value, bound_column, record):
        default = {"type": "radio", "name": bound_column.name, "value": value}
        if self.is_checked(value, record):
            default.update({"checked": "checked"})

        general = self.attrs.get("input")
        specific = self.attrs.get("td__input")
        attrs = AttributeDict(default, **(specific or general or {}))
        return mark_safe("<input %s/>" % attrs.as_html())


class ChoiceColumn(Column):
    empty_values = []

    def __init__(self, choices, widget=forms.Select, css_class='form-control', *args, **kwargs):
        self.choices = choices
        self.widget = widget
        self.css_class = css_class
        super().__init__(*args, **kwargs)

    def render(self, value):
        ff = forms.ChoiceField(choices=self.choices, widget=self.widget)
        ff.widget.attrs['class'] = self.css_class
        return ff.widget.render(self.verbose_name, value)


class CounterColumn(Column):
    empty_values = []

    def __init__(self, start=0, *args, **kwargs):
        self.start = start
        super().__init__(*args, **kwargs)

    def render(self, value):
        self.row_counter = getattr(self, 'row_counter', itertools.count())
        return self.start + next(self.row_counter)


def add_class(attrs, element, css_class):
    el = attrs.get(element, {})
    el_classes = el.get('class', '').split(' ')
    if css_class not in el_classes:
        el_classes.append(css_class)
    el['class'] = ' '.join(el_classes)
    attrs[element] = el


class NumberColumn(Column):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        add_class(attrs, 'td', 'text-right')
        add_class(attrs, 'tf', 'text-right')
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class CurrencyColumn(NumberColumn):

    def __init__(self, human_format=False, *args, **kwargs):
        self.human_format = human_format
        super().__init__(*args, **kwargs)

    def render(self, value):
        return humane_currency(value) if self.human_format else format_as_currency(value)


class HiddenIdInputColumn(Column):
    def render(self, value):
        field = forms.CharField(widget=ReadOnlyInput())
        return mark_safe(field.widget.render('id', value))