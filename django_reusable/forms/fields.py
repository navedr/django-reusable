from django import forms
import json
from ..utils.address_utils import format_us_address

caret_up_svg = '''
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-up" viewBox="0 0 16 16">
  <path d="M3.204 11h9.592L8 5.519zm-.753-.659 4.796-5.48a1 1 0 0 1 1.506 0l4.796 5.48c.566.647.106 1.659-.753 1.659H3.204a1 1 0 0 1-.753-1.659"/>
</svg>
'''

caret_down_svg = '''
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-down-fill" viewBox="0 0 16 16">
  <path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
</svg>
'''

class ChoiceFieldNoValidation(forms.ChoiceField):
    """
    An override of django's ChoiceField to ignore validation of the choices.
    Primarily used for cases where the choice fields are assigned options dynamically on the page.
    """
    def validate(self, value):
        pass


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
            'caret_up_svg': caret_up_svg,
            'caret_down_svg': caret_down_svg,
            'value': formatted_value,
        })

        return context


class USAddressFormField(forms.Field):
    """
    A form field for US addresses that renders as multiple input fields
    and validates the complete address data.
    """
    widget = USAddressWidget

    def __init__(self, *args, **kwargs):
        # Remove TextField-specific parameters that this form field doesn't use
        kwargs.pop('max_length', None)
        kwargs.pop('widget', None)  # We use our own widget
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """Convert form data to Python object"""
        if not value:
            return None

        if isinstance(value, dict):
            # Clean empty values
            cleaned_value = {}
            for key, val in value.items():
                if val and val.strip():
                    cleaned_value[key] = val.strip()

            # Return None if no meaningful data
            if not any(cleaned_value.values()):
                return None

            return cleaned_value

        return value

    def validate(self, value):
        """Validate the address data"""
        super().validate(value)

        if not value and self.required:
            raise forms.ValidationError("Address is required.")

        if not value:
            return

        # Validate required fields
        required_fields = {
            'street_address': 'Street address',
            'city': 'City',
            'state': 'State',
            'zip_code': 'ZIP code'
        }

        for field, display_name in required_fields.items():
            if field not in value or not value[field]:
                raise forms.ValidationError(f"{display_name} is required.")

        # Validate state format (2-letter code)
        if len(value['state']) != 2:
            raise forms.ValidationError("State must be a 2-letter code.")

        # Basic zip code validation
        zip_code = str(value['zip_code'])
        if not (len(zip_code) == 5 and zip_code.isdigit()) and not (
            len(zip_code) == 10 and zip_code[5] == '-' and
            zip_code[:5].isdigit() and zip_code[6:].isdigit()
        ):
            raise forms.ValidationError("ZIP code must be in format 12345 or 12345-6789.")

    def prepare_value(self, value):
        """Prepare value for display in the widget"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return value
