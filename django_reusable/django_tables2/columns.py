import itertools

from django import forms
from django.utils.safestring import mark_safe
from django_tables2 import CheckBoxColumn as DefaultCheckBoxColumn, Column
from django_tables2.utils import AttributeDict

from django_reusable.utils import global_request, humane_currency, format_as_currency
from django_reusable.forms.widgets import ReadOnlyInput


class EnhancedColumn(Column):
    """
    An enhanced version of the Django Tables2 Column with additional features.

    Args:
        new_row_index (int, optional): The index of the new row. Defaults to None.
        colspan (int, optional): The colspan attribute for the column. Defaults to None.
        no_empty_cell (bool, optional): Whether to allow empty cells. Defaults to False.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
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
        """
        Checks if the column has a new row index.

        Returns:
            bool: True if the column has a new row index, False otherwise.
        """
        return self.new_row_index is not None and self.new_row_index > 0


class TextFieldColumn(EnhancedColumn):
    """
    A column that renders a text field.
    """
    empty_values = []

    def render(self, value):
        """
        Renders the text field.

        Args:
            value (str): The value to be rendered.

        Returns:
            str: The rendered HTML of the text field.
        """
        ff = forms.CharField(widget=forms.Textarea)
        ff.widget.attrs['class'] = 'form-control'
        return ff.widget.render(self.verbose_name, value)


class EnhancedCheckBoxColumn(DefaultCheckBoxColumn):
    """
    An enhanced version of the CheckBoxColumn with additional features.
    """

    def select_checked(self, value, record):
        """
        Selects the checked value.

        Args:
            value (str): The value to be checked.
            record (object): The record to be checked.

        Returns:
            bool: True if the value is selected, False otherwise.
        """
        request = global_request()
        selected_ids = dict(request.POST).get(self.bound_column, [])
        return str(value) in selected_ids

    def __init__(self, header=None, attrs=None, checked=None, bound_column=None, **extra):
        """
        Initializes the EnhancedCheckBoxColumn.

        Args:
            header (str, optional): The header text. Defaults to None.
            attrs (dict, optional): The attributes for the column. Defaults to None.
            checked (callable, optional): The function to check if the value is selected. Defaults to None.
            bound_column (str, optional): The bound column name. Defaults to None.
            **extra: Arbitrary keyword arguments.
        """
        self._header = header
        self.bound_column = bound_column
        checked = checked or self.select_checked
        super().__init__(attrs, checked, **extra)

    @property
    def header(self):
        """
        Returns the header for the column.

        Returns:
            str: The header text.
        """
        attrs = self.attrs.get("th__input", {})
        attrs["onchange"] = '''$(this).parents('table').find(
        `tr td:nth-child(${$(this).parents("th").index() + 1}) input`
        ).prop("checked", this.checked);
        '''
        self.attrs["th__input"] = attrs
        header = self._header or super().header
        return header


class RadioButtonColumn(DefaultCheckBoxColumn):
    """
    A column that renders a radio button.
    """

    @property
    def header(self):
        """
        Returns an empty header for the radio button column.

        Returns:
            str: An empty string.
        """
        return ''

    def render(self, value, bound_column, record):
        """
        Renders the radio button.

        Args:
            value (str): The value to be rendered.
            bound_column (str): The bound column name.
            record (object): The record to be rendered.

        Returns:
            str: The rendered HTML of the radio button.
        """
        default = {"type": "radio", "name": bound_column.name, "value": value}
        if self.is_checked(value, record):
            default.update({"checked": "checked"})

        general = self.attrs.get("input")
        specific = self.attrs.get("td__input")
        attrs = AttributeDict(default, **(specific or general or {}))
        return mark_safe("<input %s/>" % attrs.as_html())


class ChoiceColumn(EnhancedColumn):
    """
    A column that renders a choice field.

    Args:
        choices (list): The choices for the field.
        widget (Widget, optional): The widget for the field. Defaults to forms.Select.
        css_class (str, optional): The CSS class for the field. Defaults to 'form-control'.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    empty_values = []

    def __init__(self, choices, widget=forms.Select, css_class='form-control', *args, **kwargs):
        self.choices = choices
        self.widget = widget
        self.css_class = css_class
        super().__init__(*args, **kwargs)

    def render(self, value):
        """
        Renders the choice field.

        Args:
            value (str): The value to be rendered.

        Returns:
            str: The rendered HTML of the choice field.
        """
        ff = forms.ChoiceField(choices=self.choices, widget=self.widget)
        ff.widget.attrs['class'] = self.css_class
        return ff.widget.render(self.verbose_name, value)


class CounterColumn(EnhancedColumn):
    """
    A column that renders a counter.

    Args:
        start (int, optional): The starting value of the counter. Defaults to 0.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    empty_values = []

    def __init__(self, start=0, *args, **kwargs):
        self.start = start
        super().__init__(*args, **kwargs)

    def render(self, value):
        """
        Renders the counter.

        Args:
            value (str): The value to be rendered.

        Returns:
            int: The current value of the counter.
        """
        self.row_counter = getattr(self, 'row_counter', itertools.count())
        return self.start + next(self.row_counter)


def add_class(attrs, element, css_class):
    """
    Adds a CSS class to the specified element in the attributes dictionary.

    Args:
        attrs (dict): The attributes dictionary.
        element (str): The element to which the CSS class will be added.
        css_class (str): The CSS class to be added.

    Returns:
        None
    """
    el = attrs.get(element, {})
    el_classes = el.get('class', '').split(' ')
    if css_class not in el_classes:
        el_classes.append(css_class)
    el['class'] = ' '.join(el_classes)
    attrs[element] = el


class NumberColumn(EnhancedColumn):
    """
    A column that renders a number with right-aligned text.
    """

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        add_class(attrs, 'td', 'text-right')
        add_class(attrs, 'tf', 'text-right')
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class CurrencyColumn(NumberColumn):
    """
    A column that renders a currency value.

    Args:
        human_format (bool, optional): Whether to use human-readable format. Defaults to False.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def __init__(self, human_format=False, *args, **kwargs):
        self.human_format = human_format
        super().__init__(*args, **kwargs)

    def render(self, value):
        """
        Renders the currency value.

        Args:
            value (float): The value to be rendered.

        Returns:
            str: The rendered currency value.
        """
        return humane_currency(value) if self.human_format else format_as_currency(value)


class HiddenIdInputColumn(EnhancedColumn):
    """
    A column that renders a hidden ID input field.
    """

    def render(self, value):
        """
        Renders the hidden ID input field.

        Args:
            value (str): The value to be rendered.

        Returns:
            str: The rendered HTML of the hidden ID input field.
        """
        field = forms.CharField(widget=ReadOnlyInput())
        return mark_safe(field.widget.render('id', value))
