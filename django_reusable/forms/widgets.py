import json
import os

from django import forms
from django.utils.safestring import mark_safe

from django_reusable.utils import xstr
from django_reusable.utils.address_utils import format_us_address


class FileLinkWidget(forms.TextInput):
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
    def render(self, name, value, attrs=None, renderer=None):
        matches = [t for (v, t) in self.choices if v == value]
        text = matches[0] if matches else None
        return f'''{xstr(text, '---')}<input name="{name}" value="{value}" type="hidden" />'''


class ReadonlyMultiSelect(forms.SelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        value_list = value if isinstance(value, list) or isinstance(value, tuple) else eval(value)
        matches = [t for (v, t) in self.choices if v in value_list]
        text = ', '.join(matches) if matches else None
        attrs = attrs or {}
        attrs['style'] = 'display: none;'
        default_widget = super().render(name, value, attrs, renderer)
        return f'''{xstr(text, '---')}{default_widget}'''


class ReadOnlyInput(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs['style'] = 'display: none;'
        return f'{xstr(value)}{super().render(name, value, attrs, renderer)}'


class DateInput(forms.DateInput):
    input_type = 'date'


class SingleCharSplitInput(forms.TextInput):
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
    """
    A widget that renders multiple input fields for US address components.
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
