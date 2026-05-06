import json
import os

from django import forms
from django.utils.safestring import mark_safe

from django_reusable.utils import xstr
from django_reusable.utils.address_utils import format_us_address


class FileLinkWidget(forms.TextInput):
    """TextInput with an adjacent "Open" link to the file if it exists on disk.

    Renders a standard text input alongside a link button that opens the file
    in a new tab, constructed from ``base_url`` + the field value.

    Args:
        base_path: Filesystem directory to check for file existence.
        base_url: URL prefix used to build the download/view link.
    """
    def __init__(self, base_path, base_url, attrs=None):
        self.base_path = base_path
        self.base_url = base_url
        super(FileLinkWidget, self).__init__(attrs)

    def get_link(self, value):
        if value and os.path.exists(os.path.join(self.base_path, value)):
            return mark_safe('<a href="%s" target="_blank" class="btn btn-default">Open</a>' %
                             os.path.join(self.base_url, value))
        return ''

    def render(self, name, value, attrs=None, renderer=None):
        html = '''
            <div class="input-group">
                %s
                <span class="input-group-btn"> 
                    %s
                </span>
            </div>
        ''' % (super().render(name, value, attrs, renderer), self.get_link(value))
        return html


class ReadonlySelect(forms.Select):
    """Select widget that displays the selected choice as plain text.

    Renders the display text of the selected value with a hidden input to
    preserve the value on form submission.
    """
    def render(self, name, value, attrs=None, renderer=None):
        matches = [t for (v, t) in self.choices if v == value]
        text = matches[0] if matches else None
        return f'''{xstr(text, '---')}<input name="{name}" value="{value}" type="hidden" />'''


class ReadonlyMultiSelect(forms.SelectMultiple):
    """SelectMultiple widget that displays selected choices as comma-separated text.

    The actual ``<select>`` element is hidden; a visible text representation is
    shown alongside it so the values are still submitted with the form.
    """
    def render(self, name, value, attrs=None, renderer=None):
        value_list = value if isinstance(value, list) or isinstance(value, tuple) else eval(value)
        matches = [t for (v, t) in self.choices if v in value_list]
        text = ', '.join(matches) if matches else None
        attrs = attrs or {}
        attrs['style'] = 'display: none;'
        default_widget = super().render(name, value, attrs, renderer)
        return f'''{xstr(text, '---')}{default_widget}'''


class ReadOnlyInput(forms.TextInput):
    """TextInput that displays the value as plain text with a hidden input.

    The visible text cannot be edited; the hidden ``<input>`` preserves the
    value for form submission. Used by ``ReadOnlyModelForm``.
    """
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs['style'] = 'display: none;'
        return f'{xstr(value)}{super().render(name, value, attrs, renderer)}'


class DateInput(forms.DateInput):
    """DateInput that renders as an HTML5 ``<input type="date">`` element."""
    input_type = 'date'


class SingleCharSplitInput(forms.TextInput):
    """TextInput that splits entry into individual single-character boxes.

    Renders ``split`` number of 1-character ``<input>`` elements. As each
    character is typed, focus advances to the next box. The concatenated value
    is stored in a hidden input for form submission.

    Args:
        split: Number of single-character input boxes (default 2).
    """
    def __init__(self, split=2, *args, **kwargs):
        self.split = split
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        split_input_attrs = attrs.copy()
        split_input_attrs.update({
            'minlength': 1,
            'maxlength': 1,
            'style': 'width: 20px; margin-right: 3px;',
            'class': 'form-control split-char',
            'id': '',
        })
        attrs_str = " ".join([f'{k}="{v}"' for (k, v) in split_input_attrs.items()])
        inputs = [f'<input {attrs_str} />' for x in range(0, self.split)]
        attrs['style'] = 'display: none;'
        return '''
                <script>
                    $(document).ready(function () {
                        $('input.split-char').on("keyup", function(){
                            if($(this).val().length == $(this).attr("maxlength")){
                                $(this).next().focus();
                                $("#id_%s").val(Array.from($('input.split-char')).map(x => x.value).join(''));
                            }
                        }); 
                    })
                </script>
               ''' % (name,) + f'''    
            <div class='single-char-split-inputs'>
                <div>{"".join(inputs)}</div>
                {super().render(name, value, attrs, renderer)}
            </div>
        '''


class USAddressWidget(forms.Widget):
    """Widget that renders five separate inputs for US address entry.

    Displays fields for street address, street address line 2, city, a state
    dropdown (all 50 US states), and ZIP code. Data is submitted as a dict
    with keys ``street_address``, ``street_address_2``, ``city``, ``state``,
    ``zip_code``.

    Uses template ``django_reusable/widgets/us_address_widget.html``.
    """
    template_name = 'django_reusable/widgets/us_address_widget.html'

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def format_value(self, value):
        """Format the value for display in the widget"""
        if value is None:
            return {
                'street_address': '',
                'street_address_2': '',
                'city': '',
                'state': '',
                'zip_code': ''
            }

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return {
                    'street_address': '',
                    'street_address_2': '',
                    'city': '',
                    'state': '',
                    'zip_code': ''
                }

        if isinstance(value, dict):
            return {
                'street_address': value.get('street_address', ''),
                'street_address_2': value.get('street_address_2', ''),
                'city': value.get('city', ''),
                'state': value.get('state', ''),
                'zip_code': value.get('zip_code', '')
            }

        return {
            'street_address': '',
            'street_address_2': '',
            'city': '',
            'state': '',
            'zip_code': ''
        }

    def value_from_datadict(self, data, files, name):
        """Extract address data from form submission"""
        return {
            'street_address': data.get(f'{name}_street_address', ''),
            'street_address_2': data.get(f'{name}_street_address_2', ''),
            'city': data.get(f'{name}_city', ''),
            'state': data.get(f'{name}_state', ''),
            'zip_code': data.get(f'{name}_zip_code', '')
        }

    def get_context(self, name, value, attrs):
        """Get context for template rendering"""
        context = super().get_context(name, value, attrs)

        formatted_value = self.format_value(value)
        formatted_display = format_us_address(formatted_value)

        # US states list
        us_states = [
            ('', '-- State --'),
            ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
            ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
            ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
            ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
            ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
            ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
            ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
            ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
            ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
            ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
            ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
            ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
            ('WI', 'Wisconsin'), ('WY', 'Wyoming')
        ]

        context.update({
            'formatted_display': formatted_display,
            'us_states': us_states,
            'value': formatted_value,
        })

        return context


class CurrencyInput(forms.TextInput):
    """TextInput with client-side US currency formatting.

    Adds a ``currency-input`` CSS class and includes
    ``django_reusable/js/currency-format.js`` which formats the value with
    ``$`` sign and comma separators on blur. The raw numeric value is preserved
    for form submission.
    """

    class Media:
        js = ('django_reusable/js/currency-format.js',)

    def __init__(self, attrs=None):
        default_attrs = {'class': 'currency-input form-control'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def format_value(self, value):
        """Format the value for display - keep as plain number for form processing"""
        if value is None or value == '':
            return ''
        try:
            # Just return the numeric value, let JavaScript handle the display formatting
            return str(float(value))
        except (ValueError, TypeError):
            return str(value) if value else ''
