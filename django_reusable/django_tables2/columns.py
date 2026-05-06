import itertools

from django import forms
from django.utils.safestring import mark_safe
from django_tables2 import CheckBoxColumn as DefaultCheckBoxColumn, Column
from django_tables2.utils import AttributeDict

from django_reusable.utils import global_request, humane_currency, format_as_currency
from django_reusable.forms.widgets import ReadOnlyInput


class EnhancedColumn(Column):
    """Extended django-tables2 Column with support for multi-row rendering and colspan.

    Args:
        new_row_index: If set to a positive int, this column's value is rendered
            in an additional row below the main row at the given index.
        colspan: Optional HTML colspan attribute for the ``<td>`` element.
        no_empty_cell: If True, skip rendering this cell when the value is empty.
    """

    def __init__(self,
                 new_row_index: int = None,
                 colspan: int = None,
                 no_empty_cell: bool = False,
                 *args, **kwargs):
        self.new_row_index = new_row_index
        self.no_empty_cell = no_empty_cell
        super().__init__(*args, **kwargs)
        if colspan:
            td_attrs = self.attrs.get('td', {})
            td_attrs['colspan'] = colspan
            self.attrs['td'] = td_attrs
        if self.has_new_row_index:
            self.visible = False

    @property
    def has_new_row_index(self):
        return self.new_row_index is not None and self.new_row_index > 0


class TextFieldColumn(EnhancedColumn):
    """Column that renders as a ``<textarea>`` form input."""

    empty_values = []

    def render(self, value):
        ff = forms.CharField(widget=forms.Textarea)
        ff.widget.attrs['class'] = 'form-control'
        return ff.widget.render(self.verbose_name, value)


class EnhancedCheckBoxColumn(DefaultCheckBoxColumn):
    """Checkbox column with select-all header toggle and POST-state preservation.

    Args:
        header: Optional custom header text.
        attrs: HTML attribute dict.
        checked: Callable to determine checked state. Defaults to reading from POST data.
        bound_column: Column name used to read selected IDs from POST.
    """

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
    """Column that renders as a radio button input (single selection per column)."""

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


class ChoiceColumn(EnhancedColumn):
    """Column that renders as a ``<select>`` dropdown.

    Args:
        choices: Iterable of ``(value, label)`` tuples for the select options.
        widget: Form widget class to use. Defaults to ``forms.Select``.
        css_class: CSS class for the widget. Defaults to ``'form-control'``.
    """

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


class CounterColumn(EnhancedColumn):
    """Column that renders an auto-incrementing row counter.

    Args:
        start: Starting number for the counter. Defaults to 0.
    """

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


class NumberColumn(EnhancedColumn):
    """Column with right-aligned text styling for numeric values."""

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        add_class(attrs, 'td', 'text-right')
        add_class(attrs, 'tf', 'text-right')
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class CurrencyColumn(NumberColumn):
    """Right-aligned column that formats values as currency.

    Args:
        human_format: If True, use abbreviated format (e.g. ``$1.5M``).
            Defaults to False (standard ``$1,500,000.00`` format).
    """

    def __init__(self, human_format=False, *args, **kwargs):
        self.human_format = human_format
        super().__init__(*args, **kwargs)

    def render(self, value):
        return humane_currency(value) if self.human_format else format_as_currency(value)


class HiddenIdInputColumn(EnhancedColumn):
    """Column that renders a read-only hidden input containing the row's ID value."""

    def render(self, value):
        field = forms.CharField(widget=ReadOnlyInput())
        return mark_safe(field.widget.render('id', value))
