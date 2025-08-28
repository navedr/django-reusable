from django import forms
import json


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

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget HTML"""
        from html import escape

        if attrs is None:
            attrs = {}

        formatted_value = self.format_value(value)

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

        html = f'''
        <div class="us-address-widget" style="border: 1px solid #ddd; padding: 10px; border-radius: 4px; display: inline-block;">
            <div>
                <label for="{name}_street_address" style="display: block; font-weight: bold; margin-bottom: 5px;">Street Address:</label>
                <input type="text" id="{name}_street_address" name="{name}_street_address" 
                       value="{escape(formatted_value.get('street_address', ''))}" 
                       autocomplete="address-line1">
            </div>
            
            <div style="margin-top: 5px;">
                <label for="{name}_street_address_2" style="display: block; font-weight: bold; margin-bottom: 5px;">Street Address 2 (Optional):</label>
                <input type="text" id="{name}_street_address_2" name="{name}_street_address_2" 
                       value="{escape(formatted_value.get('street_address_2', ''))}" 
                       autocomplete="address-line2">
            </div>
            
            <div style="margin-top: 5px;">
                <label for="{name}_city" style="display: block; font-weight: bold; margin-bottom: 5px;">City:</label>
                <input type="text" id="{name}_city" name="{name}_city" 
                       value="{escape(formatted_value.get('city', ''))}" 
                       autocomplete="address-level2">
            </div>
            <div style="display: flex; gap: 10px; margin-top: 5px;">
                <div style="flex: 1;">
                    <label for="{name}_state" style="display: block; font-weight: bold; margin-bottom: 5px;">State:</label>
                    <select id="{name}_state" name="{name}_state" style="width: 100px;"
                            autocomplete="address-level1">
        '''

        # Add state options
        for value_code, display_name in us_states:
            selected = 'selected' if value_code == formatted_value.get('state', '') else ''
            html += f'<option value="{value_code}" {selected}>{display_name}</option>'

        html += f'''
                    </select>
                </div>
                
                <div style="flex: 1;">
                    <label for="{name}_zip_code" style="display: block; font-weight: bold; margin-bottom: 5px;">ZIP Code:</label>
                    <input type="text" id="{name}_zip_code" name="{name}_zip_code" style="width: 100px;" 
                           value="{escape(formatted_value.get('zip_code', ''))}" 
                           autocomplete="postal-code"
                           placeholder="12345 or 12345-6789">
                </div>
            </div>
        </div>
        '''

        return html


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
