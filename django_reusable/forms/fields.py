from django import forms
import json

from .widgets import USAddressWidget


class ChoiceFieldNoValidation(forms.ChoiceField):
    """
    An override of django's ChoiceField to ignore validation of the choices.
    Primarily used for cases where the choice fields are assigned options dynamically on the page.
    """

    def validate(self, value):
        pass


class CheckboxMultipleChoiceField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        kwargs.pop('max_length', None)
        kwargs.pop('widget', None)  # We use our own widget
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """Override to handle JSON string values properly"""
        if not value:
            return []

        # If it's already a list, return it
        if isinstance(value, list):
            return [str(item) for item in value]

        # If it's a JSON string, parse it
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
                else:
                    return [str(parsed)]
            except json.JSONDecodeError:
                return [str(value)]

        return [str(value)]

    def validate(self, value):
        """Override validation to handle our custom data format"""
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'], code='required')

        # Validate each choice
        if value and self.choices:
            valid_choices = [str(choice[0]) for choice in self.choices]
            for item in value:
                if str(item) not in valid_choices:
                    raise forms.ValidationError(
                        self.error_messages['invalid_choice'],
                        code='invalid_choice',
                        params={'value': item},
                    )

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, forms.CheckboxSelectMultiple):
            attrs['class'] = (attrs.get('class', '') + ' unstyled').strip()
        return attrs


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
